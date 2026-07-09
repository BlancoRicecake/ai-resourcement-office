/**
 * compareReport — deterministic diff/preservation-check/rationale assembly
 * (design.md §2-2: "결정론 조립·검증 — 영속화 없음"). Pure: no persistence,
 * no LLM calls. §2-3 compare_report inputSchema caps (after.length<=50,
 * rewritten_text<=20000 chars, rationale<=2000 chars) are enforced here as
 * runtime validation, not just documented.
 */

import { MAX_AFTER_ITEMS, MAX_RATIONALE_LEN, MAX_REWRITTEN_TEXT_LEN, MAX_SECTION_ID_LEN } from "./constants.js";
import { checkPreservation } from "./prep-context.js";
import type { CompareReportInput, CompareReportResult, DiffEntry, RationaleRow } from "./types.js";

export class CompareReportValidationError extends Error {}

export function compareReport(input: CompareReportInput): CompareReportResult {
  if (input.after.length > MAX_AFTER_ITEMS) {
    throw new CompareReportValidationError(`after[] exceeds max ${MAX_AFTER_ITEMS} items (§2-3 compare_report)`);
  }

  const diff: DiffEntry[] = [];
  const rationaleTable: RationaleRow[] = [];
  const missingAcrossAll: string[] = [];

  for (const item of input.after) {
    if (item.sectionId.length > MAX_SECTION_ID_LEN) {
      throw new CompareReportValidationError(`section_id exceeds ${MAX_SECTION_ID_LEN} chars`);
    }
    if (item.rewrittenText.length > MAX_REWRITTEN_TEXT_LEN) {
      throw new CompareReportValidationError(`rewritten_text exceeds ${MAX_REWRITTEN_TEXT_LEN} chars`);
    }
    if (item.rationale !== undefined && item.rationale.length > MAX_RATIONALE_LEN) {
      throw new CompareReportValidationError(`rationale exceeds ${MAX_RATIONALE_LEN} chars`);
    }

    const originalSection = input.before.sections.find((s) => s.id === item.sectionId);
    const beforeText = originalSection?.text ?? "";

    diff.push({
      sectionId: item.sectionId,
      before: beforeText,
      after: item.rewrittenText,
      changed: beforeText !== item.rewrittenText,
    });

    if (item.rationale) {
      rationaleTable.push({ sectionId: item.sectionId, rationale: item.rationale });
    }

    // H10: testimonials/proof/quotes/stats must survive a rewrite verbatim.
    if (originalSection) {
      const { missing } = checkPreservation({ originalSection, rewrittenText: item.rewrittenText });
      missingAcrossAll.push(...missing);
    }
  }

  return {
    diff,
    preservation: { ok: missingAcrossAll.length === 0, missing: missingAcrossAll },
    rationaleTable,
  };
}
