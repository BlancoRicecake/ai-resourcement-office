/**
 * Core-owned deterministic constants (design.md §3 problem table + §5 security).
 * These are intentionally exported so tests and later adapters can assert
 * against the same thresholds instead of re-declaring magic numbers.
 */

// --- 문제표 #4: parse_quality thresholds ---
export const PARSE_QUALITY_EMPTY_CHAR_THRESHOLD = 200;
export const PARSE_QUALITY_EMPTY_SECTION_THRESHOLD = 0;
export const PARSE_QUALITY_SPARSE_CHAR_THRESHOLD = 1000;
export const PARSE_QUALITY_SPARSE_SECTION_THRESHOLD = 2;

// --- 문제표 #18: mojibake ---
export const MOJIBAKE_RATIO_THRESHOLD = 0.05;

// --- 문제표 #3: bot-block / challenge signatures ---
export const CHALLENGE_SIGNATURES: readonly string[] = [
  "just a moment",
  "cf-challenge",
  "access denied",
  "enable javascript and cookies",
  "checking your browser before accessing",
  "captcha",
  "recaptcha",
  "hcaptcha",
];

// --- 문제표 #17: redirect loop ---
export const MAX_REDIRECTS = 10;

// --- fetch_page defaults (§2-3 schema) ---
export const DEFAULT_TIMEOUT_MS = 10_000;
export const MIN_TIMEOUT_MS = 1_000;
export const MAX_TIMEOUT_MS = 30_000;
export const DEFAULT_MAX_BYTES = 5_000_000;

// --- §2-3 schema size caps mirrored as code-level validation ---
export const MAX_NAME_LEN = 80;
export const MAX_ID_LEN = 80;
export const MAX_SECTION_ID_LEN = 40;
export const MAX_REWRITTEN_TEXT_LEN = 20_000;
export const MAX_RATIONALE_LEN = 2_000;
export const MAX_AFTER_ITEMS = 50;
export const MAX_REMEMBER_CONTENT_LEN = 2_000;
export const MAX_REMEMBER_CONTEXT_LEN = 2_000;
export const MAX_WORKFLOW_STEPS = 50;
export const MAX_WORKFLOW_STEP_LEN = 500;
/** `parsed_page` arg total serialized size cap (§2-3 주석). */
export const MAX_PARSED_PAGE_SERIALIZED_BYTES = 2_000_000;

// --- ReDoS / quadratic-parse hardening (html-parser.ts) ---
// `parse_sections` receives up to DEFAULT_MAX_BYTES (5 MB) of attacker HTML.
// A hard input cap bounds total work regardless of tag density; bounding the
// lazy `[\s\S]*?` spans below additionally prevents any single unclosed
// <script>/<style>/<a>/<button> tag from making the regex scan to the end of
// the (capped) string. Chosen well below the 5 MB fetch cap — sane for real
// landing pages (typically well under 300 KB of markup).
export const MAX_PARSE_SECTIONS_INPUT_CHARS = 300_000;
/** Max chars a single <script>/<style> block's lazy scan will search before giving up on that occurrence. */
export const SCRIPT_STYLE_MAX_SPAN = 5_000;
/** Max chars a single <button>/<a> inner-text lazy scan will search before giving up on that occurrence. */
export const CTA_MAX_SPAN = 2_000;

// --- readability_scorecard: jargon term list (deterministic, not exhaustive) ---
export const JARGON_TERMS: readonly string[] = [
  "leverage",
  "synergy",
  "paradigm",
  "holistic",
  "disruptive",
  "disrupt",
  "ecosystem",
  "seamless",
  "robust",
  "scalable",
  "innovative",
  "cutting-edge",
  "cutting edge",
  "best-in-class",
  "world-class",
  "turnkey",
  "bandwidth",
  "low-hanging fruit",
  "value-add",
  "streamline",
  "empower",
  "unlock",
  "revolutionize",
  "game-changer",
  "game changer",
  "next-generation",
  "next generation",
  "state-of-the-art",
  "frictionless",
  "actionable insights",
  "circle back",
];

// --- CTA detection (parse_sections) ---
export const CTA_KEYWORD_HINTS: readonly string[] = [
  "cta",
  "btn",
  "button",
  "signup",
  "sign-up",
  "buy",
  "subscribe",
  "checkout",
];

export const CTA_PHRASES: readonly string[] = [
  "sign up",
  "get started",
  "buy now",
  "subscribe",
  "try free",
  "try it free",
  "start free trial",
  "start your free trial",
  "learn more",
  "submit",
  "book a demo",
  "request a demo",
  "contact us",
  "download",
  "join now",
  "add to cart",
  "shop now",
  "claim your",
  "get a quote",
];

// --- proof/testimonial detection (parse_sections + checkPreservation) ---
export const PROOF_KEYWORD_HINTS: readonly string[] = [
  "testimonial",
  "review",
  "proof",
  "trusted",
  "case-study",
  "case study",
  "customers say",
  "quote",
];

// --- FAQ detection ---
export const FAQ_KEYWORD_HINTS: readonly string[] = ["faq", "frequently asked", "questions"];

// --- 성장 레이어 위생 규칙 (§6-4) — referenced by later phase, kept here for
// single-source-of-truth once growth layer lands. Not used by this phase's code. ---
export const GROWTH_FORBIDDEN_PHRASE_CAP = 100;
export const GROWTH_DECISION_LOG_CAP = 500;

// --- knowledge graph (search_knowledge / knowledge_neighbors / learn_knowledge) ---
/** knowledge_neighbors depth is capped here regardless of the requested depth. */
export const KNOWLEDGE_MAX_NEIGHBOR_DEPTH = 3;
export const KNOWLEDGE_DEFAULT_SEARCH_RESULTS = 10;
export const KNOWLEDGE_MAX_SEARCH_RESULTS = 50;
/** Chars of body prose returned in a search/neighbor summary snippet. */
export const KNOWLEDGE_SNIPPET_LEN = 160;
// learn_knowledge wire-input caps (mirrored in core/tool-schemas.ts, enforced by mcp/validate.ts).
export const MAX_KNOWLEDGE_QUERY_LEN = 200;
export const MAX_KNOWLEDGE_TITLE_LEN = 200;
export const MAX_KNOWLEDGE_BODY_LEN = 20_000;
export const MAX_KNOWLEDGE_TAGS = 20;
export const MAX_KNOWLEDGE_TAG_LEN = 60;
export const MAX_KNOWLEDGE_LINKS = 30;
export const MAX_KNOWLEDGE_LINK_LEN = 120;
export const MAX_KNOWLEDGE_EVIDENCE = 20;
export const MAX_KNOWLEDGE_EVIDENCE_LEN = 500;
