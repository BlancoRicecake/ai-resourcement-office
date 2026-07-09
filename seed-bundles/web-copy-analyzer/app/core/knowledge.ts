/**
 * Knowledge graph engine — isomorphic + pure (원칙①: no fs, no Node APIs).
 *
 * Knowledge is a set of markdown NODES (YAML-ish frontmatter + prose body).
 * `[[wikilinks]]` inside a body are EDGES. Two physical roots feed one merged
 * graph (see growth/knowledge-store.ts for the Node-side fs adapter):
 *   - seed:    worker/knowledge/*.md — curated, verified, read-only, replaced
 *              on bundle update. confidence "high".
 *   - learned: ~/.web-copy-analyzer/knowledge/*.md — self-learned at runtime,
 *              provenance-tagged, survives bundle updates. starts "low".
 * `buildGraph` merges nodes from both roots into ONE queryable graph; every
 * node keeps its `source` so provenance stays visible.
 *
 * Frontmatter parse/serialize here is a small self-contained implementation
 * (block-style string arrays + scalars + `[]`), deliberately NOT importing
 * growth/frontmatter.ts — core must not depend on the growth layer (the
 * dependency direction is growth -> core). It mirrors that module's proven
 * shape so learned nodes written via serializeKnowledgeNode round-trip.
 */

import {
  KNOWLEDGE_MAX_NEIGHBOR_DEPTH,
  KNOWLEDGE_DEFAULT_SEARCH_RESULTS,
  KNOWLEDGE_MAX_SEARCH_RESULTS,
  KNOWLEDGE_SNIPPET_LEN,
} from "./constants.js";

// ---------------------------------------------------------------------------
// types
// ---------------------------------------------------------------------------

export type KnowledgeSource = "seed" | "learned";
export type KnowledgeConfidence = "high" | "medium" | "low";

export interface KnowledgeNode {
  /** kebab/slug id, unique, == filename without .md. */
  id: string;
  title: string;
  tags: string[];
  source: KnowledgeSource;
  confidence: KnowledgeConfidence;
  /** ISO date (YYYY-MM-DD) — learned nodes only; seed may omit. */
  created?: string;
  /** Learned nodes: short strings / urls backing the claim. */
  evidence: string[];
  body: string;
}

export interface KnowledgeEdge {
  from: string;
  to: string;
}

export interface KnowledgeGraph {
  nodes: Map<string, KnowledgeNode>;
  /** Directed edges from `[[wikilinks]]` (deduped). May reference a `to` that is not (yet) a node — see findDanglingEdges. */
  edges: KnowledgeEdge[];
}

export interface KnowledgeNodeSummary {
  id: string;
  title: string;
  tags: string[];
  source: KnowledgeSource;
  snippet: string;
}

export interface KnowledgeNeighbor extends KnowledgeNodeSummary {
  /** BFS distance from the query node (1..depth). */
  depth: number;
}

export interface KnowledgeNeighborsResult {
  node: KnowledgeNodeSummary;
  neighbors: KnowledgeNeighbor[];
  /** Directed edges among the visited set that were traversed. */
  edges: KnowledgeEdge[];
}

export class KnowledgeParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "KnowledgeParseError";
  }
}

/** Thrown when knowledge_neighbors is asked for an id that isn't in the merged graph. */
export class KnowledgeNodeNotFoundError extends Error {
  constructor(
    public readonly id: string,
    public readonly available: string[]
  ) {
    super(
      available.length > 0
        ? `'${id}' 지식 노드가 없습니다. 사용 가능한 노드: ${available.join(", ")}`
        : `'${id}' 지식 노드가 없습니다.`
    );
    this.name = "KnowledgeNodeNotFoundError";
  }
}

// ---------------------------------------------------------------------------
// frontmatter (self-contained; block arrays + scalars + [])
// ---------------------------------------------------------------------------

const FENCE = "---";

interface ParsedFrontmatter {
  data: Record<string, string | string[]>;
  body: string;
}

function parseFrontmatter(raw: string): ParsedFrontmatter {
  const lines = raw.split(/\r?\n/);
  if (lines[0] !== FENCE) {
    throw new KnowledgeParseError("missing opening frontmatter fence");
  }
  let i = 1;
  const data: Record<string, string | string[]> = {};
  while (i < lines.length && lines[i] !== FENCE) {
    const line = lines[i];
    if (line === undefined) throw new KnowledgeParseError("unexpected end of frontmatter");
    if (line.trim().length === 0) {
      i++;
      continue;
    }
    const scalarMatch = /^([a-zA-Z_][a-zA-Z0-9_]*):\s*(\[\])?\s*(.*)$/.exec(line);
    if (!scalarMatch) {
      throw new KnowledgeParseError(`malformed frontmatter line: ${JSON.stringify(line)}`);
    }
    const key = scalarMatch[1] as string;
    const emptyArrayMarker = scalarMatch[2];
    const rest = (scalarMatch[3] ?? "").trim();
    if (emptyArrayMarker === "[]") {
      data[key] = [];
      i++;
      continue;
    }
    if (rest.length > 0) {
      data[key] = rest;
      i++;
      continue;
    }
    // Array form: subsequent "  - item" lines.
    const items: string[] = [];
    i++;
    while (i < lines.length) {
      const itemLine = lines[i];
      if (itemLine === undefined) break;
      const itemMatch = /^\s{2}-\s?(.*)$/.exec(itemLine);
      if (!itemMatch) break;
      items.push((itemMatch[1] ?? "").trim());
      i++;
    }
    data[key] = items;
  }
  if (lines[i] !== FENCE) {
    throw new KnowledgeParseError("missing closing frontmatter fence");
  }
  const body = lines
    .slice(i + 1)
    .join("\n")
    .replace(/\n+$/, "");
  return { data, body };
}

function serializeFrontmatter(data: Record<string, string | string[]>, body: string): string {
  const lines: string[] = [FENCE];
  for (const [key, value] of Object.entries(data)) {
    if (Array.isArray(value)) {
      if (value.length === 0) {
        lines.push(`${key}: []`);
        continue;
      }
      lines.push(`${key}:`);
      for (const item of value) {
        lines.push(`  - ${item.replace(/\r?\n/g, " ").trim()}`);
      }
    } else {
      lines.push(`${key}: ${value.replace(/\r?\n/g, " ").trim()}`);
    }
  }
  lines.push(FENCE);
  return `${lines.join("\n")}\n${body}\n`;
}

// ---------------------------------------------------------------------------
// node parse / serialize
// ---------------------------------------------------------------------------

function asString(v: string | string[] | undefined): string {
  return typeof v === "string" ? v : "";
}

function asArray(v: string | string[] | undefined): string[] {
  if (Array.isArray(v)) return v.filter((s) => s.length > 0);
  if (typeof v === "string" && v.length > 0) return [v];
  return [];
}

function normalizeConfidence(v: string | undefined, fallback: KnowledgeConfidence): KnowledgeConfidence {
  return v === "high" || v === "medium" || v === "low" ? v : fallback;
}

export interface ParseNodeOptions {
  /** source when the frontmatter omits it (adapter passes the physical root's nature). */
  fallbackSource?: KnowledgeSource;
  fallbackConfidence?: KnowledgeConfidence;
}

/** Parse one markdown node (frontmatter + body). Throws KnowledgeParseError on malformed frontmatter or missing id/title. */
export function parseKnowledgeNode(raw: string, opts: ParseNodeOptions = {}): KnowledgeNode {
  const { data, body } = parseFrontmatter(raw);
  const id = asString(data["id"]).trim();
  const title = asString(data["title"]).trim();
  if (id.length === 0) throw new KnowledgeParseError("knowledge node missing 'id'");
  if (title.length === 0) throw new KnowledgeParseError(`knowledge node '${id}' missing 'title'`);
  const source = asString(data["source"]) === "seed" || asString(data["source"]) === "learned"
    ? (asString(data["source"]) as KnowledgeSource)
    : opts.fallbackSource ?? "seed";
  const node: KnowledgeNode = {
    id,
    title,
    tags: asArray(data["tags"]),
    source,
    confidence: normalizeConfidence(asString(data["confidence"]) || undefined, opts.fallbackConfidence ?? (source === "seed" ? "high" : "low")),
    evidence: asArray(data["evidence"]),
    body,
  };
  const created = asString(data["created"]).trim();
  if (created.length > 0) node.created = created;
  return node;
}

/** Serialize a node back to markdown (block arrays). Used by the learned-node writer so learned nodes round-trip through parseKnowledgeNode. */
export function serializeKnowledgeNode(node: KnowledgeNode): string {
  const data: Record<string, string | string[]> = {
    id: node.id,
    title: node.title,
    tags: node.tags,
    source: node.source,
    confidence: node.confidence,
  };
  if (node.created) data["created"] = node.created;
  data["evidence"] = node.evidence;
  return serializeFrontmatter(data, node.body);
}

// ---------------------------------------------------------------------------
// wikilinks / graph construction
// ---------------------------------------------------------------------------

const WIKILINK_RE = /\[\[\s*([^\[\]|]+?)\s*\]\]/g;

/** Extract unique `[[id]]` targets from a body, in first-appearance order. */
export function extractWikilinks(body: string): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const match of body.matchAll(WIKILINK_RE)) {
    const id = (match[1] ?? "").trim();
    if (id.length === 0 || seen.has(id)) continue;
    seen.add(id);
    out.push(id);
  }
  return out;
}

/**
 * Merge nodes into one graph. Seed and learned nodes coexist; on an id
 * collision the FIRST-inserted node wins (adapter inserts seed before learned,
 * so verified seed is never clobbered by a learned duplicate) — learned ids
 * are timestamp-disambiguated to avoid this in practice. Edges are the union
 * of every node's `[[wikilinks]]` (deduped, self-loops preserved so verify
 * gates can detect them; dangling targets preserved — see findDanglingEdges).
 */
export function buildGraph(nodes: KnowledgeNode[]): KnowledgeGraph {
  const map = new Map<string, KnowledgeNode>();
  for (const node of nodes) {
    if (!map.has(node.id)) map.set(node.id, node);
  }
  const edges: KnowledgeEdge[] = [];
  const seenEdge = new Set<string>();
  for (const node of map.values()) {
    for (const to of extractWikilinks(node.body)) {
      const key = `${node.id} ${to}`;
      if (seenEdge.has(key)) continue;
      seenEdge.add(key);
      edges.push({ from: node.id, to });
    }
  }
  return { nodes: map, edges };
}

/** Edges whose `to` is not a node in the graph (dangling citation). Used by the seed verify gate. */
export function findDanglingEdges(graph: KnowledgeGraph): KnowledgeEdge[] {
  return graph.edges.filter((e) => !graph.nodes.has(e.to));
}

/** Edges where from === to (self-loop). Used by the seed verify gate. */
export function findSelfLoops(graph: KnowledgeGraph): KnowledgeEdge[] {
  return graph.edges.filter((e) => e.from === e.to);
}

// ---------------------------------------------------------------------------
// search
// ---------------------------------------------------------------------------

function snippetOf(body: string): string {
  const flat = body.replace(/\s+/g, " ").trim();
  return flat.length > KNOWLEDGE_SNIPPET_LEN ? `${flat.slice(0, KNOWLEDGE_SNIPPET_LEN)}…` : flat;
}

function summarize(node: KnowledgeNode): KnowledgeNodeSummary {
  return { id: node.id, title: node.title, tags: node.tags, source: node.source, snippet: snippetOf(node.body) };
}

/**
 * Deterministic keyword+tag search over the merged graph (no LLM). Scores each
 * node per query term against id / title / tags / body, ranks descending, and
 * breaks ties by id for stable output. Returns node summaries.
 */
export function searchKnowledge(graph: KnowledgeGraph, query: string, maxResults?: number): KnowledgeNodeSummary[] {
  const limit = Math.max(1, Math.min(maxResults ?? KNOWLEDGE_DEFAULT_SEARCH_RESULTS, KNOWLEDGE_MAX_SEARCH_RESULTS));
  const q = query.trim().toLowerCase();
  if (q.length === 0) return [];
  const terms = Array.from(new Set(q.split(/\s+/).filter((t) => t.length > 0)));

  const scored: Array<{ node: KnowledgeNode; score: number }> = [];
  for (const node of graph.nodes.values()) {
    const id = node.id.toLowerCase();
    const title = node.title.toLowerCase();
    const tags = node.tags.map((t) => t.toLowerCase());
    const body = node.body.toLowerCase();
    let score = 0;
    for (const term of terms) {
      if (id === term) score += 8;
      else if (id.includes(term)) score += 5;
      if (title.includes(term)) score += 4;
      if (tags.some((t) => t.includes(term))) score += 3;
      if (body.includes(term)) score += 1;
    }
    // Whole-query bonus for a title/id direct hit.
    if (title.includes(q) || id.includes(q)) score += 2;
    if (score > 0) scored.push({ node, score });
  }

  scored.sort((a, b) => (b.score - a.score) || a.node.id.localeCompare(b.node.id));
  return scored.slice(0, limit).map((s) => summarize(s.node));
}

// ---------------------------------------------------------------------------
// neighbors (BFS)
// ---------------------------------------------------------------------------

function undirectedAdjacency(graph: KnowledgeGraph): Map<string, Set<string>> {
  const adj = new Map<string, Set<string>>();
  const link = (a: string, b: string) => {
    if (!graph.nodes.has(a) || !graph.nodes.has(b)) return;
    if (!adj.has(a)) adj.set(a, new Set());
    adj.get(a)!.add(b);
  };
  for (const e of graph.edges) {
    link(e.from, e.to);
    link(e.to, e.from);
  }
  return adj;
}

/**
 * BFS from `nodeId` out to `depth` (clamped to 1..KNOWLEDGE_MAX_NEIGHBOR_DEPTH).
 * Edges are followed bidirectionally for reachability (a `[[link]]` connects
 * both concepts), and the directed edges among the visited set are returned as
 * `edges`. Throws KnowledgeNodeNotFoundError for an unknown id.
 */
export function knowledgeNeighbors(graph: KnowledgeGraph, nodeId: string, depth?: number): KnowledgeNeighborsResult {
  const root = graph.nodes.get(nodeId);
  if (!root) {
    throw new KnowledgeNodeNotFoundError(nodeId, Array.from(graph.nodes.keys()).sort());
  }
  const maxDepth = Math.max(1, Math.min(depth ?? 1, KNOWLEDGE_MAX_NEIGHBOR_DEPTH));
  const adj = undirectedAdjacency(graph);

  const distance = new Map<string, number>([[nodeId, 0]]);
  let frontier = [nodeId];
  for (let d = 1; d <= maxDepth && frontier.length > 0; d++) {
    const next: string[] = [];
    for (const cur of frontier) {
      for (const nb of adj.get(cur) ?? []) {
        if (distance.has(nb)) continue;
        distance.set(nb, d);
        next.push(nb);
      }
    }
    next.sort();
    frontier = next;
  }

  const neighbors: KnowledgeNeighbor[] = [];
  for (const [id, d] of distance) {
    if (d === 0) continue;
    const node = graph.nodes.get(id);
    if (node) neighbors.push({ ...summarize(node), depth: d });
  }
  neighbors.sort((a, b) => (a.depth - b.depth) || a.id.localeCompare(b.id));

  const visited = new Set(distance.keys());
  const edges = graph.edges.filter((e) => visited.has(e.from) && visited.has(e.to));

  return { node: summarize(root), neighbors, edges };
}

// ---------------------------------------------------------------------------
// graph.json (prebuilt seed snapshot)
// ---------------------------------------------------------------------------

interface SerializedNode {
  id: string;
  title: string;
  tags: string[];
  source: KnowledgeSource;
  confidence: KnowledgeConfidence;
  created?: string;
  evidence: string[];
  body: string;
}

export interface SerializedGraph {
  version: number;
  nodes: SerializedNode[];
  edges: KnowledgeEdge[];
}

export const KNOWLEDGE_GRAPH_JSON_VERSION = 1;

function toSerializedNode(node: KnowledgeNode): SerializedNode {
  const out: SerializedNode = {
    id: node.id,
    title: node.title,
    tags: node.tags,
    source: node.source,
    confidence: node.confidence,
    evidence: node.evidence,
    body: node.body,
  };
  if (node.created) out.created = node.created;
  return out;
}

/** Deterministic JSON snapshot of a seed graph (nodes sorted by id, edges sorted). Round-trips: same nodes => byte-identical output. */
export function serializeGraphJson(nodes: KnowledgeNode[]): string {
  const graph = buildGraph(nodes);
  const serializedNodes = Array.from(graph.nodes.values())
    .sort((a, b) => a.id.localeCompare(b.id))
    .map(toSerializedNode);
  const edges = [...graph.edges].sort((a, b) => a.from.localeCompare(b.from) || a.to.localeCompare(b.to));
  const payload: SerializedGraph = { version: KNOWLEDGE_GRAPH_JSON_VERSION, nodes: serializedNodes, edges };
  return `${JSON.stringify(payload, null, 2)}\n`;
}

/** Parse a graph.json snapshot back into nodes. Edges are rederived by buildGraph from bodies (the serialized edges are a verifiable cache, not the source of truth). */
export function deserializeGraphNodes(json: string): KnowledgeNode[] {
  const payload = JSON.parse(json) as SerializedGraph;
  if (!payload || !Array.isArray(payload.nodes)) {
    throw new KnowledgeParseError("graph.json: missing nodes array");
  }
  return payload.nodes.map((n) => ({
    id: n.id,
    title: n.title,
    tags: Array.isArray(n.tags) ? n.tags : [],
    source: n.source === "learned" ? "learned" : "seed",
    confidence: normalizeConfidence(n.confidence, "high"),
    ...(n.created ? { created: n.created } : {}),
    evidence: Array.isArray(n.evidence) ? n.evidence : [],
    body: n.body ?? "",
  }));
}
