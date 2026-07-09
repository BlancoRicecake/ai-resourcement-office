import { test } from "node:test";
import assert from "node:assert/strict";
import { parseSections } from "../html-parser.js";
import { compareReport, CompareReportValidationError } from "../compare-report.js";

const HTML = `<html><body>
  <header><h1>Ship Faster With Acme</h1></header>
  <section class="cta"><button>Start free trial</button></section>
  <section class="testimonial"><p>"Acme cut our deploy time by 80%," says Jane, CTO of Widgets Inc.</p></section>
</body></html>`;

test("compareReport: produces a diff entry with before/after and rationale table row", () => {
  const before = parseSections({ html: HTML });
  const headline = before.sections.find((s) => s.role === "headline" || s.role === "hero")!;
  const result = compareReport({
    before,
    after: [{ sectionId: headline.id, rewrittenText: "Deploy Without Fear, DevOps Dana", rationale: "H3 clarity, H6 specificity" }],
  });
  assert.equal(result.diff.length, 1);
  assert.equal(result.diff[0]!.changed, true);
  assert.equal(result.rationaleTable.length, 1);
  assert.equal(result.rationaleTable[0]!.rationale, "H3 clarity, H6 specificity");
});

test("compareReport: 문제표 #14 — preservation.ok=false and missing[] populated when testimonial dropped", () => {
  const before = parseSections({ html: HTML });
  const proof = before.sections.find((s) => s.role === "proof")!;
  const result = compareReport({
    before,
    after: [{ sectionId: proof.id, rewrittenText: "Customers really like it." }],
  });
  assert.equal(result.preservation.ok, false);
  assert.ok(result.preservation.missing.length > 0);
});

test("compareReport: H10 — preservation.ok=true when testimonial preserved verbatim", () => {
  const before = parseSections({ html: HTML });
  const proof = before.sections.find((s) => s.role === "proof")!;
  const result = compareReport({
    before,
    after: [{ sectionId: proof.id, rewrittenText: `Jane, CTO of Widgets Inc., says: "Acme cut our deploy time by 80%," and means it.` }],
  });
  assert.equal(result.preservation.ok, true);
});

test("compareReport: rejects more than 50 after[] items (§2-3 compare_report cap)", () => {
  const before = parseSections({ html: HTML });
  const after = Array.from({ length: 51 }, (_, i) => ({ sectionId: `s${i}`, rewrittenText: "x" }));
  assert.throws(() => compareReport({ before, after }), CompareReportValidationError);
});

test("compareReport: rejects rewritten_text exceeding 20000 chars (§2-3 compare_report cap)", () => {
  const before = parseSections({ html: HTML });
  const headline = before.sections.find((s) => s.role === "headline" || s.role === "hero")!;
  assert.throws(
    () => compareReport({ before, after: [{ sectionId: headline.id, rewrittenText: "x".repeat(20001) }] }),
    CompareReportValidationError
  );
});

test("compareReport: rejects rationale exceeding 2000 chars (§2-3 compare_report cap)", () => {
  const before = parseSections({ html: HTML });
  const headline = before.sections.find((s) => s.role === "headline" || s.role === "hero")!;
  assert.throws(
    () => compareReport({ before, after: [{ sectionId: headline.id, rewrittenText: "ok", rationale: "x".repeat(2001) }] }),
    CompareReportValidationError
  );
});

test("compareReport: is pure — calling twice with same input yields identical output (no persistence)", () => {
  const before = parseSections({ html: HTML });
  const headline = before.sections.find((s) => s.role === "headline" || s.role === "hero")!;
  const input = { before, after: [{ sectionId: headline.id, rewrittenText: "New headline text" }] };
  const a = compareReport(input);
  const b = compareReport(input);
  assert.deepEqual(a, b);
});

test("compareReport: section_id not present in before.sections still produces a diff entry with empty 'before'", () => {
  const before = parseSections({ html: HTML });
  const result = compareReport({ before, after: [{ sectionId: "unknown-id", rewrittenText: "new text" }] });
  assert.equal(result.diff[0]!.before, "");
  assert.equal(result.diff[0]!.after, "new text");
});
