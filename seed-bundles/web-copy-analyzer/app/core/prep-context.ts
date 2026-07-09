/**
 * buildDiagnosisContext / buildRewriteContext — prep-tool payload builders
 * (design.md §2-1: these NEVER call an LLM; they assemble the payload the
 * host LLM will judge over: section text + persona + deterministic signals +
 * the judgment frame). checkPreservation is the deterministic verifier used
 * both standalone (§2-2) and inside compareReport (§2-3 compare_report).
 */

import { MAX_SECTION_ID_LEN } from "./constants.js";
import { PROOF_KEYWORD_HINTS } from "./constants.js";
import type {
  AttributionFrame,
  CheckPreservationInput,
  CheckPreservationResult,
  DiagnosisBrief,
  DiagnosisContextInput,
  PreservationConstraint,
  RewriteBrief,
  RewriteContextInput,
  Section,
} from "./types.js";

const ATTRIBUTION_FRAME: AttributionFrame[] = ["clarity", "trust", "relevance", "cta"];

function findSection(sections: Section[], sectionId: string | undefined): Section | undefined {
  if (sectionId === undefined) return undefined;
  return sections.find((s) => s.id === sectionId);
}

export class PrepContextError extends Error {}

export function buildDiagnosisContext(input: DiagnosisContextInput): DiagnosisBrief {
  const scope = input.scope ?? "section";

  if (scope === "above_fold") {
    const aboveFoldSections = input.parsedPage.sections.filter((s) => s.aboveFoldEstimate);
    return {
      briefKind: "diagnosis",
      section: { aboveFoldSections },
      persona: input.persona,
      deterministicSignals: {
        sectionCount: aboveFoldSections.length,
        roles: aboveFoldSections.map((s) => s.role),
      },
      attributionFrame: ATTRIBUTION_FRAME,
      // H1: 5-second test recall frame — "what/who/next action".
      instructionsHint:
        "5초 시뮬레이션: 이 above-the-fold 섹션들만 보고 '무엇을 파는가 / 누구를 위한가 / 다음 행동은' 이 회상되는지 판단하라. " +
        `페르소나 '${input.persona.name}'(${input.persona.role})의 목표·불안·어휘를 명시 인용해 귀속하라(범용 조언 금지).`,
    };
  }

  if (input.sectionId !== undefined && input.sectionId.length > MAX_SECTION_ID_LEN) {
    throw new PrepContextError(`section_id exceeds ${MAX_SECTION_ID_LEN} chars`);
  }
  const section = findSection(input.parsedPage.sections, input.sectionId);
  if (!section) {
    throw new PrepContextError(`section '${input.sectionId ?? ""}' not found in parsed_page`);
  }

  return {
    briefKind: "diagnosis",
    section,
    persona: input.persona,
    deterministicSignals: {
      role: section.role,
      textLength: section.text.length,
      aboveFoldEstimate: section.aboveFoldEstimate,
    },
    attributionFrame: ATTRIBUTION_FRAME,
    instructionsHint:
      `섹션 '${section.id}'(${section.role})을 페르소나 '${input.persona.name}'(${input.persona.role})의 ` +
      "관점에서 명확성/신뢰/관련성/CTA 중 하나로 이탈 원인을 귀속하라. 페르소나의 구체 속성을 인용하라(H11). " +
      "뭉뚱그린 총평 금지 — 원인+대안+근거로 환원하라.",
  };
}

function detectPreservationConstraints(section: Section): PreservationConstraint[] {
  const constraints: PreservationConstraint[] = [];
  const text = section.text;
  const isProofLike = section.role === "proof" || PROOF_KEYWORD_HINTS.some((k) => text.toLowerCase().includes(k));

  // Quoted spans (curly or straight quotes) are treated as verbatim customer
  // language (H10) that must survive a rewrite unmodified.
  const quoteRe = /["“]([^"”]{4,})["”]/g;
  let m: RegExpExecArray | null;
  while ((m = quoteRe.exec(text)) !== null) {
    const quoted = m[1];
    if (quoted) constraints.push({ kind: "quote", text: quoted.trim() });
  }

  // If this is a proof/testimonial-flagged section but no explicit quoted
  // span was found, fall back to requiring the whole section preserved
  // verbatim (we can't isolate the exact VoC text, so be conservative).
  // When quotes WERE found, they are the actual H10 preservation target —
  // requiring the entire section (including our own attribution wrapper
  // text) to survive unchanged would defeat the point of a "rewrite".
  if (isProofLike && constraints.length === 0) {
    constraints.push({ kind: "testimonial", text });
  }

  // Numeric stats (e.g. "40% increase", "10,000 customers") are facts that
  // must not be altered by a rewrite (§10 절대 규칙: 팩트 창작 금지).
  const statRe = /\b\d[\d,.]*\s?%?[a-zA-Z]*\b/g;
  const stats = text.match(statRe) ?? [];
  for (const stat of stats) {
    if (/\d/.test(stat)) constraints.push({ kind: "stat", text: stat });
  }

  return constraints;
}

export function buildRewriteContext(input: RewriteContextInput): RewriteBrief {
  if (input.sectionId.length > MAX_SECTION_ID_LEN) {
    throw new PrepContextError(`section_id exceeds ${MAX_SECTION_ID_LEN} chars`);
  }
  const section = findSection(input.parsedPage.sections, input.sectionId);
  if (!section) {
    throw new PrepContextError(`section '${input.sectionId}' not found in parsed_page`);
  }

  const preservationConstraints = detectPreservationConstraints(section);

  return {
    briefKind: "rewrite",
    section,
    personaVoice: {
      vocabulary: input.persona.vocabulary,
      tone: `${input.persona.role} 관점의 you-언어(H8), 구체적 결과 중심(H6)`,
    },
    preservationConstraints,
    instructionsHint:
      `섹션 '${section.id}'을 페르소나 '${input.persona.name}'의 어휘·톤으로 리라이트하라. ` +
      (preservationConstraints.length > 0
        ? `다음 ${preservationConstraints.length}개 원문 요소는 절대 변경 없이 보존하라(H10): ` +
          preservationConstraints.map((c) => `[${c.kind}] ${c.text}`).join(" / ")
        : "이 섹션에는 보존 대상 후기/증거/수치가 감지되지 않았다.") +
      " 변경마다 근거 원칙 라벨을 명시하라.",
  };
}

export function checkPreservation(input: CheckPreservationInput): CheckPreservationResult {
  const constraints = detectPreservationConstraints(input.originalSection);
  const missing: string[] = [];
  for (const constraint of constraints) {
    if (!input.rewrittenText.includes(constraint.text)) {
      missing.push(constraint.text);
    }
  }
  return { preserved: missing.length === 0, missing };
}
