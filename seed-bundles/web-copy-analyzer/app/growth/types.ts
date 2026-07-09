/**
 * Growth-layer types (design.md §6, §11). This module is Node-only and
 * stateful — it owns the `~/.web-copy-analyzer/` directory (or an injected
 * `rootDir` override for tests, see growth/paths.ts). It is intentionally
 * separate from `core/` (which stays pure/dependency-free per 원칙①); the
 * growth layer is adapter-side state that wraps `core/persona.ts`'s pure
 * `definePersona` for validation before persisting.
 */

import type { Persona, PersonaDraft } from "../core/types.js";

export const GROWTH_SCHEMA_VERSION = 1;

// ---------------------------------------------------------------------------
// personas/<slug>.md
// ---------------------------------------------------------------------------

export interface StoredPersonaMeta {
  schemaVersion: number;
  /** ISO timestamp, updated on every save (design.md §6-4: list_personas shows last-used). */
  updatedAt: string;
  /** ISO timestamp of last get_persona (§6-4 "최근 사용일"). */
  lastUsedAt?: string;
}

export interface PersonaSummary {
  id: string;
  name: string;
  role: string;
  updatedAt: string;
  lastUsedAt?: string;
}

export interface SavePersonaInput {
  draft: PersonaDraft;
  overwrite?: boolean;
}

export interface SavePersonaResult {
  saved: boolean;
  path: string;
  id: string;
  /** True when disk write failed and the persona was kept session-only (문제표 #20). */
  sessionOnly?: boolean;
  warning?: string;
}

export interface DeletePersonaResult {
  deleted: boolean;
}

/** Thrown for 문제표 #8 (persona id not found) — carries the available id list. */
export class PersonaNotFoundError extends Error {
  constructor(
    public readonly id: string,
    public readonly available: string[]
  ) {
    super(
      available.length > 0
        ? `'${id}' 페르소나가 없습니다. 저장된 목록: ${available.join(", ")}`
        : `'${id}' 페르소나가 없습니다. 저장된 페르소나가 아직 없습니다.`
    );
    this.name = "PersonaNotFoundError";
  }
}

/** Thrown for 문제표 #9 (persona file corrupt/unparseable). */
export class PersonaCorruptError extends Error {
  constructor(
    public readonly id: string,
    public override readonly cause?: unknown
  ) {
    super(`'${id}' 페르소나 파일을 읽을 수 없습니다(손상).`);
    this.name = "PersonaCorruptError";
  }
}

/** Thrown for 문제표 #22 (save_persona name collision, overwrite=false). */
export class PersonaNameCollisionError extends Error {
  constructor(public readonly id: string) {
    super(`'${id}' 페르소나가 이미 있습니다. 덮어쓸까요, 다른 이름으로 저장할까요?`);
    this.name = "PersonaNameCollisionError";
  }
}

// ---------------------------------------------------------------------------
// remember (voice.md: brand_voice/forbidden_phrase, decisions.log: persona_pref/decision)
// ---------------------------------------------------------------------------

export type MemoryKind = "persona_pref" | "brand_voice" | "forbidden_phrase" | "decision";

export interface MemoryEntryInput {
  kind: MemoryKind;
  content: string;
  context?: string;
}

/** Heuristic adoption/rejection label (design.md §11 — enables future suppression of repeated-rejection patterns). */
export type DecisionLabel = "adopted" | "rejected" | "neutral";

export interface StoredMemoryEntry {
  schemaVersion: number;
  kind: MemoryKind;
  content: string;
  context?: string;
  ts: string;
  label?: DecisionLabel;
}

export interface RememberResult {
  stored: boolean;
  shown: string;
  rejected?: boolean;
  reason?: string;
  sessionOnly?: boolean;
}

// ---------------------------------------------------------------------------
// workflows/<name>.json
// ---------------------------------------------------------------------------

export interface SaveWorkflowInput {
  name: string;
  steps: string[];
}

export interface SaveWorkflowResult {
  saved: boolean;
  path?: string;
  sessionOnly?: boolean;
  warning?: string;
}

export interface StoredWorkflow {
  schemaVersion: number;
  name: string;
  steps: string[];
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// growth snapshot (for mergeInstructions, growth/merge.ts)
// ---------------------------------------------------------------------------

export interface GrowthSnapshot {
  personas: PersonaSummary[];
  brandVoice: string[];
  forbiddenPhrases: string[];
  /** Ids/lines that failed to parse and were isolated (문제표 #10). */
  corrupted: string[];
}

export type { Persona, PersonaDraft };
