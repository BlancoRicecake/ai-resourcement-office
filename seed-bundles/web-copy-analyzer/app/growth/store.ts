/**
 * GrowthStore — stateful Node-side growth layer (design.md §6). Wraps the
 * pure core function `definePersona` for validation, then owns all file I/O
 * under `~/.web-copy-analyzer/` (or an injected rootDir for tests).
 *
 * One instance is created per MCP server process/session so that the
 * 문제표 #20 in-memory fallback (disk write failure → session-only) actually
 * persists across tool calls within that session.
 */

import * as fs from "node:fs/promises";
import { definePersona, PersonaValidationError } from "../core/persona.js";
import type { Persona } from "../core/types.js";
import { GROWTH_FORBIDDEN_PHRASE_CAP, GROWTH_DECISION_LOG_CAP } from "../core/constants.js";
import { parseFrontmatter, serializeFrontmatter, FrontmatterParseError } from "./frontmatter.js";
import { detectForbiddenContent, FORBIDDEN_MEMORY_MESSAGE } from "./hygiene.js";
import { appendEntry, readLog } from "./memory-log.js";
import {
  decisionsLogPath,
  personaFilePath,
  personasDir,
  resolveGrowthRoot,
  voiceFilePath,
  workflowFilePath,
  workflowsDir,
} from "./paths.js";
import { isStorageUnavailableError, readFileIfExists, writeFileEnsuringDir } from "./fs-utils.js";
import {
  GROWTH_SCHEMA_VERSION,
  PersonaCorruptError,
  PersonaNameCollisionError,
  PersonaNotFoundError,
  type GrowthSnapshot,
  type MemoryEntryInput,
  type PersonaSummary,
  type RememberResult,
  type SavePersonaInput,
  type SavePersonaResult,
  type SaveWorkflowInput,
  type SaveWorkflowResult,
  type StoredWorkflow,
} from "./types.js";

/** §5 "persona_id 경로 이탈(../) 차단" — reject ids that aren't a plain slug. */
function assertSafeId(id: string): void {
  if (id.length === 0 || id.length > 80 || /[/\\]|\.\./.test(id) || id !== id.trim()) {
    throw new PersonaValidationError(`invalid persona id: ${JSON.stringify(id)}`);
  }
}

function deriveDecisionLabel(content: string): "adopted" | "rejected" | "neutral" {
  const lower = content.toLowerCase();
  if (/(채택|adopt|accepted|applied|승인)/.test(lower)) return "adopted";
  if (/(거부|reject|declined|rejected|취소)/.test(lower)) return "rejected";
  return "neutral";
}

export interface GrowthStoreOptions {
  rootDir?: string;
  /** Injectable clock for deterministic tests. Defaults to `() => new Date().toISOString()`. */
  now?: () => string;
}

export class GrowthStore {
  private readonly rootDir: string;
  private readonly now: () => string;

  // Session-only fallback state (문제표 #20) — only populated when a disk
  // write fails; reads merge this on top of whatever disk has.
  private memoryPersonas = new Map<string, Persona>();
  private memoryWorkflows = new Map<string, StoredWorkflow>();
  private sessionOnlyWarnings: string[] = [];

  constructor(opts: GrowthStoreOptions = {}) {
    this.rootDir = resolveGrowthRoot(opts.rootDir);
    this.now = opts.now ?? (() => new Date().toISOString());
  }

  getRootDir(): string {
    return this.rootDir;
  }

  /** Warnings accumulated so far this session (문제표 #20 write/read fallbacks) — startup surfaces these via stderr. */
  getSessionOnlyWarnings(): string[] {
    return [...this.sessionOnlyWarnings];
  }

  // -------------------------------------------------------------------------
  // personas
  // -------------------------------------------------------------------------

  async savePersona(input: SavePersonaInput): Promise<SavePersonaResult> {
    const persona = definePersona(input.draft);
    assertSafeId(persona.id);
    const overwrite = input.overwrite ?? false;
    const filePath = personaFilePath(this.rootDir, persona.id);

    const existing = await readFileIfExists(filePath).catch(() => undefined);
    const existsOnDisk = existing !== undefined;
    const existsInMemory = this.memoryPersonas.has(persona.id);
    if ((existsOnDisk || existsInMemory) && !overwrite) {
      throw new PersonaNameCollisionError(persona.id);
    }

    const nowTs = this.now();
    const md = serializeFrontmatter(
      {
        schema_version: GROWTH_SCHEMA_VERSION,
        name: persona.name,
        role: persona.role,
        goals: persona.goals,
        pains: persona.pains,
        vocabulary: persona.vocabulary,
        buying_triggers: persona.buyingTriggers,
        updated_at: nowTs,
      },
      `# ${persona.name}\n\n${persona.role}`
    );

    try {
      await writeFileEnsuringDir(filePath, md);
      this.memoryPersonas.delete(persona.id);
      return { saved: true, path: filePath, id: persona.id };
    } catch (err) {
      if (!isStorageUnavailableError(err)) throw err;
      this.memoryPersonas.set(persona.id, persona);
      const warning = `설정 저장 공간에 쓸 수 없습니다(${(err as NodeJS.ErrnoException).code}). 이번 세션에서만 페르소나/기억이 유지됩니다.`;
      this.sessionOnlyWarnings.push(warning);
      return { saved: true, path: filePath, id: persona.id, sessionOnly: true, warning };
    }
  }

  async listPersonas(): Promise<PersonaSummary[]> {
    const summaries = new Map<string, PersonaSummary>();

    let ids: string[] = [];
    try {
      const dir = personasDir(this.rootDir);
      const files = await fs.readdir(dir).catch((err) => {
        if ((err as NodeJS.ErrnoException).code === "ENOENT") return [] as string[];
        throw err;
      });
      ids = files.filter((f) => f.endsWith(".md")).map((f) => f.slice(0, -".md".length));
    } catch {
      ids = [];
    }

    for (const id of ids) {
      try {
        const persona = await this.readPersonaFile(id);
        summaries.set(id, {
          id,
          name: persona.persona.name,
          role: persona.persona.role,
          updatedAt: persona.updatedAt,
          lastUsedAt: persona.lastUsedAt,
        });
      } catch {
        // 문제표 #9: corrupt persona file — isolate, skip, keep loading the rest.
        continue;
      }
    }

    for (const [id, persona] of this.memoryPersonas.entries()) {
      summaries.set(id, { id, name: persona.name, role: persona.role, updatedAt: this.now() });
    }

    return Array.from(summaries.values());
  }

  async getPersona(id: string): Promise<Persona> {
    assertSafeId(id);
    const memoryHit = this.memoryPersonas.get(id);
    try {
      const { persona } = await this.readPersonaFile(id);
      await this.touchLastUsed(id).catch(() => undefined);
      return persona;
    } catch (err) {
      if (memoryHit) return memoryHit;
      if (err instanceof PersonaCorruptError) throw err;
      const available = (await this.listPersonas()).map((p) => p.id);
      throw new PersonaNotFoundError(id, available);
    }
  }

  async deletePersona(id: string): Promise<{ deleted: boolean }> {
    assertSafeId(id);
    let deletedOnDisk = false;
    try {
      await fs.unlink(personaFilePath(this.rootDir, id));
      deletedOnDisk = true;
    } catch (err) {
      if ((err as NodeJS.ErrnoException).code !== "ENOENT") throw err;
    }
    const deletedInMemory = this.memoryPersonas.delete(id);
    return { deleted: deletedOnDisk || deletedInMemory };
  }

  private async readPersonaFile(id: string): Promise<{ persona: Persona; updatedAt: string; lastUsedAt?: string }> {
    const raw = await fs.readFile(personaFilePath(this.rootDir, id), "utf-8");
    let parsed: { data: Record<string, string | string[]>; body: string };
    try {
      parsed = parseFrontmatter(raw);
    } catch (err) {
      if (err instanceof FrontmatterParseError) throw new PersonaCorruptError(id, err);
      throw err;
    }
    const d = parsed.data;
    const asArray = (v: string | string[] | undefined): string[] => (Array.isArray(v) ? v : v ? [v] : []);
    const asString = (v: string | string[] | undefined): string => (typeof v === "string" ? v : "");
    if (!asString(d["name"]) || !asString(d["role"])) {
      throw new PersonaCorruptError(id);
    }
    const persona: Persona = {
      id,
      name: asString(d["name"]),
      role: asString(d["role"]),
      goals: asArray(d["goals"]),
      pains: asArray(d["pains"]),
      vocabulary: asArray(d["vocabulary"]),
      buyingTriggers: asArray(d["buying_triggers"]),
    };
    return {
      persona,
      updatedAt: asString(d["updated_at"]) || "",
      lastUsedAt: asString(d["last_used_at"]) || undefined,
    };
  }

  private async touchLastUsed(id: string): Promise<void> {
    const raw = await fs.readFile(personaFilePath(this.rootDir, id), "utf-8");
    const { data, body } = parseFrontmatter(raw);
    data["last_used_at"] = this.now();
    const md = serializeFrontmatter(data as Record<string, string | number | string[]>, body);
    await writeFileEnsuringDir(personaFilePath(this.rootDir, id), md);
  }

  // -------------------------------------------------------------------------
  // remember (문제표 #11 hygiene, §6-4 dedup/caps)
  // -------------------------------------------------------------------------

  async remember(input: MemoryEntryInput): Promise<RememberResult> {
    const contentCheck = detectForbiddenContent(input.content);
    const contextCheck = input.context ? detectForbiddenContent(input.context) : { forbidden: false as const };
    if (contentCheck.forbidden || contextCheck.forbidden) {
      return { stored: false, shown: FORBIDDEN_MEMORY_MESSAGE, rejected: true, reason: FORBIDDEN_MEMORY_MESSAGE };
    }

    const isVoiceKind = input.kind === "brand_voice" || input.kind === "forbidden_phrase";
    const filePath = isVoiceKind ? voiceFilePath(this.rootDir) : decisionsLogPath(this.rootDir);
    const cap = input.kind === "forbidden_phrase" ? GROWTH_FORBIDDEN_PHRASE_CAP : input.kind === "decision" ? GROWTH_DECISION_LOG_CAP : undefined;

    const entry = {
      schemaVersion: GROWTH_SCHEMA_VERSION,
      kind: input.kind,
      content: input.content,
      context: input.context,
      ts: this.now(),
      label: input.kind === "decision" || input.kind === "persona_pref" ? deriveDecisionLabel(input.content) : undefined,
    };

    try {
      await appendEntry(filePath, entry, cap !== undefined ? { capForKind: cap } : {});
      const shown = `기억함: ${input.content}`;
      return { stored: true, shown };
    } catch (err) {
      if (!isStorageUnavailableError(err)) throw err;
      const warning = `설정 저장 공간에 쓸 수 없습니다(${(err as NodeJS.ErrnoException).code}). 이번 세션에서만 페르소나/기억이 유지됩니다.`;
      this.sessionOnlyWarnings.push(warning);
      return { stored: true, shown: `기억함(세션 내): ${input.content}`, sessionOnly: true };
    }
  }

  // -------------------------------------------------------------------------
  // workflows
  // -------------------------------------------------------------------------

  async saveWorkflow(input: SaveWorkflowInput): Promise<SaveWorkflowResult> {
    assertSafeId(input.name);
    const filePath = workflowFilePath(this.rootDir, input.name);
    const stored: StoredWorkflow = {
      schemaVersion: GROWTH_SCHEMA_VERSION,
      name: input.name,
      steps: input.steps,
      updatedAt: this.now(),
    };
    try {
      await writeFileEnsuringDir(filePath, JSON.stringify(stored, null, 2));
      this.memoryWorkflows.delete(input.name);
      return { saved: true, path: filePath };
    } catch (err) {
      if (!isStorageUnavailableError(err)) throw err;
      this.memoryWorkflows.set(input.name, stored);
      const warning = `설정 저장 공간에 쓸 수 없습니다(${(err as NodeJS.ErrnoException).code}). 이번 세션에서만 워크플로가 유지됩니다.`;
      this.sessionOnlyWarnings.push(warning);
      return { saved: true, sessionOnly: true, warning };
    }
  }

  async listWorkflowNames(): Promise<string[]> {
    const dir = workflowsDir(this.rootDir);
    const onDisk = await fs
      .readdir(dir)
      .then((files) => files.filter((f) => f.endsWith(".json")).map((f) => f.slice(0, -".json".length)))
      .catch((err) => {
        if ((err as NodeJS.ErrnoException).code === "ENOENT") return [] as string[];
        throw err;
      });
    return Array.from(new Set([...onDisk, ...this.memoryWorkflows.keys()]));
  }

  // -------------------------------------------------------------------------
  // growth snapshot (for mergeInstructions, growth/merge.ts)
  // -------------------------------------------------------------------------

  async buildGrowthSnapshot(): Promise<GrowthSnapshot> {
    const personas = await this.listPersonas();
    // 문제표 #20: a storage-unavailable READ error (EACCES/ENOSPC/EROFS/EPERM
    // on voice.md, e.g. a permission-mangled growth root) must degrade to an
    // empty/session-only snapshot with a warning instead of propagating and
    // crashing startup — same class of error, same predicate, as the write
    // paths above (savePersona/remember/saveWorkflow). ENOENT (missing file)
    // is already handled as "no entries" inside readLog/readFileIfExists and
    // is not an error here. A genuinely unexpected error still throws.
    let entries: Awaited<ReturnType<typeof readLog>>["entries"] = [];
    let corrupted: string[] = [];
    try {
      ({ entries, corrupted } = await readLog(voiceFilePath(this.rootDir)));
    } catch (err) {
      if (!isStorageUnavailableError(err)) throw err;
      const warning = `설정 저장 공간을 읽을 수 없습니다(${(err as NodeJS.ErrnoException).code}). 이번 세션은 저장된 브랜드 보이스/금지 문구 없이 시작합니다.`;
      this.sessionOnlyWarnings.push(warning);
    }
    const brandVoice = entries.filter((e) => e.kind === "brand_voice").map((e) => e.content);
    const forbiddenPhrases = entries.filter((e) => e.kind === "forbidden_phrase").map((e) => e.content);
    return { personas, brandVoice, forbiddenPhrases, corrupted };
  }
}
