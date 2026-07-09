/**
 * KnowledgeStore — Node-side adapter for the knowledge graph (the fs half of
 * the isomorphic core/knowledge.ts, mirroring the core-vs-fetch-node split).
 *
 * It reads TWO physical roots and merges them into ONE queried graph:
 *   - seed:    the bundle's worker/knowledge/ — verified, read-only. Loaded
 *              from the prebuilt graph.json snapshot when present (the shipped
 *              artifact), else parsed live from the .md dir (source tree).
 *   - learned: ~/.web-copy-analyzer/knowledge/ (growth root) — self-learned at
 *              runtime, parsed LIVE every query so a learn_knowledge write is
 *              immediately searchable and survives restart (the whole point).
 *
 * learn_knowledge writes ONLY into the learned root, after the same
 * growth/hygiene.ts filter that gates remember() (customer PII / undisclosed
 * revenue are rejected, never bypassed).
 */

import * as fs from "node:fs/promises";
import { existsSync } from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildGraph,
  deserializeGraphNodes,
  knowledgeNeighbors,
  parseKnowledgeNode,
  searchKnowledge,
  serializeKnowledgeNode,
  type KnowledgeGraph,
  type KnowledgeNode,
  type KnowledgeNeighborsResult,
  type KnowledgeNodeSummary,
} from "../core/knowledge.js";
import { PersonaValidationError } from "../core/persona.js";
import { detectForbiddenContent, FORBIDDEN_MEMORY_MESSAGE } from "./hygiene.js";
import { knowledgeDir, knowledgeNodePath, resolveGrowthRoot } from "./paths.js";
import { isStorageUnavailableError, readFileIfExists, writeFileEnsuringDir } from "./fs-utils.js";

const MODULE_DIR = path.dirname(fileURLToPath(import.meta.url));

/**
 * Seed graph.json — prefer the bundled copy next to this module (build.mjs
 * copies worker/knowledge/graph.json into dist/, same dir as the flattened
 * bundle), else the source-tree location. Mirrors server.ts defaultAgentsMdPath.
 */
export function defaultSeedGraphPath(): string {
  const bundled = path.join(MODULE_DIR, "graph.json");
  if (existsSync(bundled)) return bundled;
  return path.join(MODULE_DIR, "..", "..", "worker", "knowledge", "graph.json");
}

/** Seed .md directory (source-tree fallback when no graph.json snapshot exists). */
export function defaultSeedKnowledgeDir(): string {
  return path.join(MODULE_DIR, "..", "..", "worker", "knowledge");
}

/** §5 path-traversal hardening — same semantics as store.ts assertSafeId (allow Korean/spaces, block / \\ .. and untrimmed). */
function assertSafeKnowledgeId(id: string): void {
  if (id.length === 0 || id.length > 120 || /[/\\]|\.\./.test(id) || id !== id.trim()) {
    throw new PersonaValidationError(`invalid knowledge node id: ${JSON.stringify(id)}`);
  }
}

/** Slug a title into an id that keeps Korean/Unicode letters but is filename- and wikilink-safe. */
function knowledgeSlug(title: string): string {
  const slug = title
    .trim()
    .toLowerCase()
    .replace(/[\s/\\]+/g, "-")
    .replace(/[^\p{L}\p{N}-]+/gu, "-")
    .replace(/-+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug.length > 0 ? slug : "note";
}

export interface LearnKnowledgeInput {
  title: string;
  body: string;
  tags?: string[];
  links?: string[];
  evidence?: string[];
}

export interface LearnKnowledgeResult {
  learned: boolean;
  id?: string;
  path?: string;
  shown: string;
  rejected?: boolean;
  reason?: string;
  sessionOnly?: boolean;
  warning?: string;
}

export interface KnowledgeStoreOptions {
  /** Growth-layer (learned) root override — tests only. */
  rootDir?: string;
  /** Seed graph.json snapshot path override — tests only. */
  seedGraphPath?: string;
  /** Seed .md dir override (used when seedGraphPath is absent) — tests only. */
  seedDir?: string;
  /** Injectable clock. Defaults to `() => new Date().toISOString()`. */
  now?: () => string;
}

export class KnowledgeStore {
  private readonly rootDir: string;
  private readonly seedGraphPath: string;
  private readonly seedDir: string;
  private readonly now: () => string;

  // Session-only fallback for learned nodes when the growth root is unwritable
  // (문제표 #20 parity) — merged into the query graph so a learn during a
  // read-only session is still searchable that session.
  private memoryLearned = new Map<string, KnowledgeNode>();
  private sessionOnlyWarnings: string[] = [];

  constructor(opts: KnowledgeStoreOptions = {}) {
    this.rootDir = resolveGrowthRoot(opts.rootDir);
    this.seedGraphPath = opts.seedGraphPath ?? defaultSeedGraphPath();
    this.seedDir = opts.seedDir ?? defaultSeedKnowledgeDir();
    this.now = opts.now ?? (() => new Date().toISOString());
  }

  getSessionOnlyWarnings(): string[] {
    return [...this.sessionOnlyWarnings];
  }

  // -------------------------------------------------------------------------
  // loading
  // -------------------------------------------------------------------------

  /** Seed nodes from the graph.json snapshot if present, else parsed live from the seed .md dir. */
  async loadSeedNodes(): Promise<KnowledgeNode[]> {
    const snapshot = await readFileIfExists(this.seedGraphPath).catch(() => undefined);
    if (snapshot !== undefined) {
      try {
        return deserializeGraphNodes(snapshot);
      } catch {
        // Corrupt snapshot — fall through to the .md dir rather than crash.
      }
    }
    return this.loadNodesFromDir(this.seedDir, "seed");
  }

  /** Learned nodes read live from the growth root's knowledge/ dir + any session-only in-memory nodes. */
  async loadLearnedNodes(): Promise<KnowledgeNode[]> {
    const onDisk = await this.loadNodesFromDir(knowledgeDir(this.rootDir), "learned");
    const ids = new Set(onDisk.map((n) => n.id));
    const merged = [...onDisk];
    for (const [id, node] of this.memoryLearned) {
      if (!ids.has(id)) merged.push(node);
    }
    return merged;
  }

  /** Merged seed+learned graph (seed inserted first so it wins any id collision). */
  async loadGraph(): Promise<KnowledgeGraph> {
    const [seed, learned] = await Promise.all([this.loadSeedNodes(), this.loadLearnedNodes()]);
    return buildGraph([...seed, ...learned]);
  }

  private async loadNodesFromDir(dir: string, fallbackSource: "seed" | "learned"): Promise<KnowledgeNode[]> {
    let files: string[];
    try {
      files = await fs.readdir(dir);
    } catch (err) {
      if ((err as NodeJS.ErrnoException).code === "ENOENT") return [];
      throw err;
    }
    const nodes: KnowledgeNode[] = [];
    for (const file of files) {
      if (!file.endsWith(".md")) continue;
      try {
        const raw = await fs.readFile(path.join(dir, file), "utf-8");
        const node = parseKnowledgeNode(raw, {
          fallbackSource,
          fallbackConfidence: fallbackSource === "seed" ? "high" : "low",
        });
        nodes.push(node);
      } catch {
        // 문제표 #9 parity: isolate a corrupt node file, keep loading the rest.
        continue;
      }
    }
    return nodes;
  }

  // -------------------------------------------------------------------------
  // query
  // -------------------------------------------------------------------------

  async searchKnowledge(query: string, maxResults?: number): Promise<KnowledgeNodeSummary[]> {
    const graph = await this.loadGraph();
    return searchKnowledge(graph, query, maxResults);
  }

  async knowledgeNeighbors(nodeId: string, depth?: number): Promise<KnowledgeNeighborsResult> {
    const graph = await this.loadGraph();
    return knowledgeNeighbors(graph, nodeId, depth);
  }

  // -------------------------------------------------------------------------
  // learn (writes a new learned node — hygiene-gated)
  // -------------------------------------------------------------------------

  async learnKnowledge(input: LearnKnowledgeInput): Promise<LearnKnowledgeResult> {
    const title = input.title.trim();
    const body = input.body.trim();
    if (title.length === 0) throw new PersonaValidationError("learn_knowledge: title is required");
    if (body.length === 0) throw new PersonaValidationError("learn_knowledge: body is required");

    // Same hygiene gate as remember() — customer PII / undisclosed revenue are
    // rejected here too (§4 규칙과 일관), never persisted, never bypassed.
    const evidence = (input.evidence ?? []).map((e) => e.trim()).filter((e) => e.length > 0);
    const links = (input.links ?? []).map((l) => l.trim()).filter((l) => l.length > 0);
    const hygieneTarget = [title, body, ...evidence, ...links].join("\n");
    if (detectForbiddenContent(hygieneTarget).forbidden) {
      return { learned: false, rejected: true, shown: FORBIDDEN_MEMORY_MESSAGE, reason: FORBIDDEN_MEMORY_MESSAGE };
    }

    const nowIso = this.now();
    const created = nowIso.slice(0, 10);
    const disambiguator = nowIso.replace(/[^0-9]/g, "").slice(0, 14) || "0";
    const id = `${knowledgeSlug(title)}-${disambiguator}`;
    assertSafeKnowledgeId(id);

    // `links` become [[wikilinks]] appended to the body (edges).
    const linkLine = links.length > 0 ? `\n\n관련: ${links.map((l) => `[[${l}]]`).join(" ")}` : "";
    const node: KnowledgeNode = {
      id,
      title,
      tags: (input.tags ?? []).map((t) => t.trim()).filter((t) => t.length > 0),
      source: "learned",
      confidence: "low",
      created,
      evidence,
      body: `${body}${linkLine}`,
    };

    const filePath = knowledgeNodePath(this.rootDir, id);
    const md = serializeKnowledgeNode(node);
    try {
      await writeFileEnsuringDir(filePath, md);
      this.memoryLearned.delete(id);
      return { learned: true, id, path: filePath, shown: `학습함: ${title}` };
    } catch (err) {
      if (!isStorageUnavailableError(err)) throw err;
      this.memoryLearned.set(id, node);
      const warning = `설정 저장 공간에 쓸 수 없습니다(${(err as NodeJS.ErrnoException).code}). 이번 세션에서만 학습 지식이 유지됩니다.`;
      this.sessionOnlyWarnings.push(warning);
      return { learned: true, id, path: filePath, shown: `학습함(세션 내): ${title}`, sessionOnly: true, warning };
    }
  }
}
