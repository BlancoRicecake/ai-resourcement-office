import { test } from "node:test";
import assert from "node:assert/strict";
import { parseSections } from "../html-parser.js";
import { definePersona } from "../persona.js";
import { buildDiagnosisContext, buildRewriteContext, checkPreservation, PrepContextError } from "../prep-context.js";

const HTML = `<html><body>
  <header><h1>Ship Faster With Acme</h1><p>Built for teams who hate downtime.</p></header>
  <section class="cta"><button>Start free trial</button></section>
  <section class="testimonial"><p>"Acme cut our deploy time by 80%," says Jane, CTO of Widgets Inc.</p></section>
</body></html>`;

const PERSONA = definePersona({
  name: "DevOps Dana",
  role: "DevOps lead",
  pains: ["flaky deploys"],
  vocabulary: ["CI/CD", "rollback"],
});

test("buildDiagnosisContext: section scope returns a prep payload, not a judgment", () => {
  const parsed = parseSections({ html: HTML });
  const ctaSection = parsed.sections.find((s) => s.role === "cta")!;
  const brief = buildDiagnosisContext({ parsedPage: parsed, sectionId: ctaSection.id, persona: PERSONA, scope: "section" });
  assert.equal(brief.briefKind, "diagnosis");
  assert.deepEqual(brief.attributionFrame, ["clarity", "trust", "relevance", "cta"]);
  assert.ok(brief.instructionsHint.length > 0);
  // Must NOT contain any judgment/verdict fields — it's a payload, not a diagnosis result.
  assert.ok(!("verdict" in brief));
});

test("buildDiagnosisContext: above_fold scope aggregates above-the-fold sections (H1/H2)", () => {
  const parsed = parseSections({ html: HTML });
  const brief = buildDiagnosisContext({ parsedPage: parsed, persona: PERSONA, scope: "above_fold" });
  assert.ok("aboveFoldSections" in brief.section);
});

test("buildDiagnosisContext: unknown section_id throws PrepContextError", () => {
  const parsed = parseSections({ html: HTML });
  assert.throws(() => buildDiagnosisContext({ parsedPage: parsed, sectionId: "does-not-exist", persona: PERSONA }), PrepContextError);
});

test("buildRewriteContext: surfaces preservation constraints for a testimonial section (H10)", () => {
  const parsed = parseSections({ html: HTML });
  const proofSection = parsed.sections.find((s) => s.role === "proof")!;
  const brief = buildRewriteContext({ parsedPage: parsed, sectionId: proofSection.id, persona: PERSONA });
  assert.equal(brief.briefKind, "rewrite");
  assert.ok(brief.preservationConstraints.length > 0);
  assert.ok(brief.preservationConstraints.some((c) => c.kind === "testimonial" || c.kind === "quote" || c.kind === "stat"));
});

test("buildRewriteContext: unknown section_id throws PrepContextError", () => {
  const parsed = parseSections({ html: HTML });
  assert.throws(() => buildRewriteContext({ parsedPage: parsed, sectionId: "nope", persona: PERSONA }), PrepContextError);
});

test("checkPreservation: 문제표 #14 — flags missing testimonial/stat when rewrite drops it", () => {
  const parsed = parseSections({ html: HTML });
  const proofSection = parsed.sections.find((s) => s.role === "proof")!;
  const result = checkPreservation({ originalSection: proofSection, rewrittenText: "Our customers love how fast deploys are now." });
  assert.equal(result.preserved, false);
  assert.ok(result.missing.length > 0);
});

test("checkPreservation: passes when the rewrite preserves the quoted testimonial verbatim", () => {
  const parsed = parseSections({ html: HTML });
  const proofSection = parsed.sections.find((s) => s.role === "proof")!;
  const rewritten = `As Jane, CTO of Widgets Inc. puts it: "Acme cut our deploy time by 80%," and that's why we love it.`;
  const result = checkPreservation({ originalSection: proofSection, rewrittenText: rewritten });
  assert.equal(result.preserved, true);
  assert.deepEqual(result.missing, []);
});
