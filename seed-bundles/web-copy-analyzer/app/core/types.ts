/**
 * Shared types for the isomorphic core (design.md §2-2).
 *
 * NOTE on naming: MCP tool I/O over the wire uses snake_case (design.md §2-3,
 * mirrored verbatim in tool-schemas.ts). Internal TS function signatures use
 * idiomatic camelCase. Mapping between the two is an *adapter* concern
 * (later phase: MCP server), not a core concern — keeping the core
 * snake_case-free avoids leaking wire-format assumptions into pure logic.
 */

// ---------------------------------------------------------------------------
// parse_sections
// ---------------------------------------------------------------------------

export type SectionRole =
  | "hero"
  | "headline"
  | "subhead"
  | "cta"
  | "proof"
  | "feature"
  | "faq"
  | "footer"
  | "other";

export interface Section {
  id: string;
  role: SectionRole;
  text: string;
  domIndex: number;
  aboveFoldEstimate: boolean;
}

export type ParseQuality = "rich" | "sparse" | "empty";

export interface ParsedPage {
  sections: Section[];
  /** Section ids in DOM appearance order (design.md §2-2 `domOrder`). */
  domOrder: string[];
  parseQuality: ParseQuality;
  /** Ratio of U+FFFD replacement chars to total chars (mojibake signal, 문제표 #18). */
  mojibakeRatio: number;
  /** True if the input `html` exceeded MAX_PARSE_SECTIONS_INPUT_CHARS and was truncated before parsing. */
  truncated?: boolean;
}

export interface ParseSectionsInput {
  html: string;
  baseUrl?: string;
}

// ---------------------------------------------------------------------------
// readability_scorecard
// ---------------------------------------------------------------------------

export interface StructureChecklistItem {
  item: string;
  pass: boolean;
}

export interface CtaInventoryItem {
  text: string;
  domIndex: number;
}

export interface Scorecard {
  language: string;
  englishDependentMetricsApplicable: boolean;
  readability: {
    gradeLevel: number;
    avgSentenceLen: number;
  };
  structureChecklist: StructureChecklistItem[];
  ctaInventory: CtaInventoryItem[];
  headlineLength: {
    chars: number;
    words: number;
  };
  weYouRatio: {
    we: number;
    you: number;
    ratio: number;
  };
  jargonDensity: {
    jargonTerms: number;
    per100Words: number;
  };
}

// ---------------------------------------------------------------------------
// personas (definePersona is pure; storage I/O is a later-phase growth-layer
// adapter concern per design.md §2-1 — see core/persona.ts header comment)
// ---------------------------------------------------------------------------

export interface PersonaDraft {
  name: string;
  role: string;
  goals?: string[];
  pains: string[];
  vocabulary: string[];
  buyingTriggers?: string[];
}

export interface Persona {
  id: string;
  name: string;
  role: string;
  goals: string[];
  pains: string[];
  vocabulary: string[];
  buyingTriggers: string[];
}

// ---------------------------------------------------------------------------
// diagnose_section / rewrite_section (prep-tools — context builders, no LLM)
// ---------------------------------------------------------------------------

export type AttributionFrame = "clarity" | "trust" | "relevance" | "cta";

export interface DiagnosisContextInput {
  parsedPage: ParsedPage;
  sectionId?: string;
  persona: Persona;
  scope?: "section" | "above_fold";
}

export interface DiagnosisBrief {
  briefKind: "diagnosis";
  section: Section | { aboveFoldSections: Section[] };
  persona: Persona;
  deterministicSignals: Record<string, unknown>;
  attributionFrame: AttributionFrame[];
  instructionsHint: string;
}

export interface RewriteContextInput {
  parsedPage: ParsedPage;
  sectionId: string;
  persona: Persona;
}

export type PreservationKind = "testimonial" | "proof" | "stat" | "quote";

export interface PreservationConstraint {
  kind: PreservationKind;
  text: string;
}

export interface RewriteBrief {
  briefKind: "rewrite";
  section: Section;
  personaVoice: {
    vocabulary: string[];
    tone: string;
  };
  preservationConstraints: PreservationConstraint[];
  instructionsHint: string;
}

// ---------------------------------------------------------------------------
// check_preservation / compare_report
// ---------------------------------------------------------------------------

export interface CheckPreservationInput {
  originalSection: Section;
  rewrittenText: string;
}

export interface CheckPreservationResult {
  preserved: boolean;
  missing: string[];
}

export interface CompareReportAfterItem {
  sectionId: string;
  rewrittenText: string;
  rationale?: string;
}

export interface CompareReportInput {
  before: ParsedPage;
  after: CompareReportAfterItem[];
}

export interface DiffEntry {
  sectionId: string;
  before: string;
  after: string;
  changed: boolean;
}

export interface RationaleRow {
  sectionId: string;
  rationale: string;
}

export interface CompareReportResult {
  diff: DiffEntry[];
  preservation: {
    ok: boolean;
    missing: string[];
  };
  rationaleTable: RationaleRow[];
}

// ---------------------------------------------------------------------------
// fetch_page (Node-only — see core/fetch-node.ts)
// ---------------------------------------------------------------------------

/**
 * Matches design.md §2-3 fetch_page.outputSchema.error_kind enum EXACTLY —
 * do not add values here. SSRF blocks and redirect loops are mapped onto
 * this fixed vocabulary in fetch-node.ts ("blocked" and "network"
 * respectively) rather than growing the enum.
 */
export type FetchErrorKind = "not_found" | "timeout" | "blocked" | "too_large" | "non_html" | "network" | "ok";

export interface FetchPageOptions {
  url: string;
  timeoutMs?: number;
  maxBytes?: number;
  allowLocal?: boolean;
}

export interface FetchResult {
  ok: boolean;
  status: number;
  finalUrl: string;
  contentType: string;
  bytes: number;
  html: string;
  error?: string;
  errorKind: FetchErrorKind;
  /** Ratio of U+FFFD replacement chars after decode (mojibake signal, 문제표 #18). */
  mojibakeRatio?: number;
  /** True if a challenge/bot-block signature was detected (문제표 #3). */
  challengeDetected?: boolean;
  /** True if `html` was truncated to maxBytes (문제표 #5). */
  truncated?: boolean;
}
