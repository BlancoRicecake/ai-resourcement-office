/**
 * Append-only JSONL log backing voice.md (brand_voice/forbidden_phrase) and
 * decisions.log (persona_pref/decision) — design.md §6-1, §6-4.
 *
 * Format note (ambiguity resolved): design.md describes these as markdown/
 * plain-text append logs. This implementation stores one JSON object per
 * line (JSONL) with a `schema_version` header line — this keeps parsing
 * exact and lets 문제표 #10 ("손상 라인만 격리, 나머지 병합 진행") isolate a
 * single corrupt line without risking a hand-rolled markdown parser
 * misreading adjacent valid entries. The file is still user-readable plain
 * text (§5 "평문이라 사용자 열람·삭제 가능"), just JSON-per-line instead of
 * markdown-per-line.
 */

import { GROWTH_SCHEMA_VERSION } from "./types.js";
import type { StoredMemoryEntry } from "./types.js";
import { atomicAppendLine, readFileIfExists, writeFileEnsuringDir } from "./fs-utils.js";

const SCHEMA_HEADER_PREFIX = "schema_version:";

export interface ReadLogResult {
  entries: StoredMemoryEntry[];
  /** Raw corrupt lines, isolated per 문제표 #10 — the rest of the file still loads. */
  corrupted: string[];
}

export async function readLog(filePath: string): Promise<ReadLogResult> {
  const raw = await readFileIfExists(filePath);
  if (raw === undefined) return { entries: [], corrupted: [] };

  const lines = raw.split(/\r?\n/).filter((l) => l.trim().length > 0);
  const entries: StoredMemoryEntry[] = [];
  const corrupted: string[] = [];
  for (const line of lines) {
    if (line.startsWith(SCHEMA_HEADER_PREFIX)) continue;
    try {
      const parsed = JSON.parse(line) as Partial<StoredMemoryEntry>;
      if (
        typeof parsed.kind !== "string" ||
        typeof parsed.content !== "string" ||
        typeof parsed.ts !== "string" ||
        typeof parsed.schemaVersion !== "number"
      ) {
        corrupted.push(line);
        continue;
      }
      entries.push(parsed as StoredMemoryEntry);
    } catch {
      corrupted.push(line);
    }
  }
  return { entries, corrupted };
}

function normalize(content: string): string {
  return content.trim().toLowerCase().replace(/\s+/g, " ");
}

async function rewriteLog(filePath: string, entries: StoredMemoryEntry[]): Promise<void> {
  const body = entries.map((e) => JSON.stringify(e)).join("\n");
  const content = `${SCHEMA_HEADER_PREFIX}${GROWTH_SCHEMA_VERSION}\n${body}${body.length > 0 ? "\n" : ""}`;
  await writeFileEnsuringDir(filePath, content);
}

export interface AppendEntryOptions {
  /** kind-scoped cap (§6-4: forbidden_phrase 100, decision 500). Overflow is archived to `${filePath}.archive`. */
  capForKind?: number;
}

export interface AppendEntryResult {
  /** true when an existing duplicate (same kind + normalized content) was updated in place instead of appended. */
  deduped: boolean;
}

/**
 * Appends (or, for a normalized duplicate, updates in place — §6-4 "중복
 * 병합"). New, non-duplicate entries take the atomic-append fast path (the
 * one 문제표 #21 concurrency guarantees cover); duplicate updates take a
 * read-modify-write rewrite path, which is not contended in the tested
 * scenario (concurrent *distinct* new entries).
 */
export async function appendEntry(filePath: string, entry: StoredMemoryEntry, opts: AppendEntryOptions = {}): Promise<AppendEntryResult> {
  const existingRaw = await readFileIfExists(filePath);
  const { entries } = await readLog(filePath);
  const normalizedNew = normalize(entry.content);
  const dupIndex = entries.findIndex((e) => e.kind === entry.kind && normalize(e.content) === normalizedNew);

  if (dupIndex >= 0) {
    entries[dupIndex] = entry;
    await rewriteLog(filePath, entries);
    return { deduped: true };
  }

  if (existingRaw === undefined) {
    // First write to this file: emit the schema_version header before the
    // first entry line, atomically, so a fresh file is never headerless.
    await atomicAppendLine(filePath, `${SCHEMA_HEADER_PREFIX}${GROWTH_SCHEMA_VERSION}`);
  }
  await atomicAppendLine(filePath, JSON.stringify(entry));

  if (opts.capForKind !== undefined) {
    await enforceCap(filePath, entry.kind, opts.capForKind);
  }
  return { deduped: false };
}

async function enforceCap(filePath: string, kind: StoredMemoryEntry["kind"], cap: number): Promise<void> {
  const { entries } = await readLog(filePath);
  const ofKind = entries.filter((e) => e.kind === kind);
  if (ofKind.length <= cap) return;

  const sorted = [...ofKind].sort((a, b) => a.ts.localeCompare(b.ts));
  const overflowCount = sorted.length - cap;
  const overflow = sorted.slice(0, overflowCount);
  const overflowIds = new Set(overflow);

  const kept = entries.filter((e) => !(e.kind === kind && overflowIds.has(e)));
  await rewriteLog(filePath, kept);

  const archivePath = `${filePath}.archive`;
  for (const e of overflow) {
    await atomicAppendLine(archivePath, JSON.stringify(e));
  }
}
