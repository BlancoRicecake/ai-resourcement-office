import { test } from "node:test";
import assert from "node:assert/strict";
import { parseSections } from "../html-parser.js";
import { readabilityScorecard } from "../readability.js";

const ENGLISH_HTML = `<html><body>
  <header><h1>We Help You Ship Faster</h1><p>Our platform gives you the tools you need to deploy your code with confidence, every single day.</p></header>
  <section class="cta"><button class="btn-primary">Get started</button></section>
  <section class="testimonial"><p>"This tool changed how we ship," says Sam.</p></section>
  <footer><p>Contact us</p></footer>
</body></html>`;

const KOREAN_HTML = `<html><body>
  <header><h1>더 빠르게 배포하세요</h1><p>우리 플랫폼은 팀이 매일 자신 있게 코드를 배포할 수 있도록 도와줍니다.</p></header>
  <section class="cta"><button>지금 시작하기</button></section>
  <footer><p>문의하기</p></footer>
</body></html>`;

test("readabilityScorecard: English page marks english_dependent_metrics_applicable=true", () => {
  const parsed = parseSections({ html: ENGLISH_HTML });
  const scorecard = readabilityScorecard(parsed);
  assert.equal(scorecard.language, "en");
  assert.equal(scorecard.englishDependentMetricsApplicable, true);
});

test("readabilityScorecard: 문제표 #19 — non-English page gates English-dependent metrics off but still returns language-neutral metrics", () => {
  const parsed = parseSections({ html: KOREAN_HTML });
  const scorecard = readabilityScorecard(parsed);
  assert.equal(scorecard.language, "ko");
  assert.equal(scorecard.englishDependentMetricsApplicable, false);
  // Language-neutral metrics must still be populated normally.
  assert.ok(scorecard.structureChecklist.length > 0);
  assert.ok(Array.isArray(scorecard.ctaInventory));
  assert.ok(scorecard.headlineLength.chars > 0);
});

test("readabilityScorecard: single CTA passes the 1:1 attention-ratio checklist item (H4)", () => {
  const parsed = parseSections({ html: ENGLISH_HTML });
  const scorecard = readabilityScorecard(parsed);
  const check = scorecard.structureChecklist.find((c) => c.item === "single_primary_cta");
  assert.ok(check);
  assert.equal(check!.pass, true);
});

test("readabilityScorecard: multiple CTAs fail the attention-ratio checklist item (H4)", () => {
  const html = `<html><body><header><h1>Too Many Choices</h1></header>
    <a href="/a" class="btn">Buy now</a><a href="/b" class="btn">Sign up</a><a href="/c" class="btn">Learn more</a>
  </body></html>`;
  const parsed = parseSections({ html });
  const scorecard = readabilityScorecard(parsed);
  const check = scorecard.structureChecklist.find((c) => c.item === "single_primary_cta");
  assert.equal(check!.pass, false);
});

test("readabilityScorecard: we/you ratio counts both pronouns (H8)", () => {
  const parsed = parseSections({ html: ENGLISH_HTML });
  const scorecard = readabilityScorecard(parsed);
  assert.ok(scorecard.weYouRatio.we > 0);
  assert.ok(scorecard.weYouRatio.you > 0);
});

test("readabilityScorecard: jargon density counts known buzzwords", () => {
  const html = `<html><body><header><h1>Leverage Our Synergy</h1><p>We leverage a holistic, robust, scalable ecosystem to empower your seamless workflow.</p></header></body></html>`;
  const parsed = parseSections({ html });
  const scorecard = readabilityScorecard(parsed);
  assert.ok(scorecard.jargonDensity.jargonTerms >= 5, `expected several jargon hits, got ${scorecard.jargonDensity.jargonTerms}`);
});

test("readabilityScorecard: determinism — same ParsedPage produces identical scorecard", () => {
  const parsed = parseSections({ html: ENGLISH_HTML });
  const a = readabilityScorecard(parsed);
  const b = readabilityScorecard(parsed);
  assert.deepEqual(a, b);
});

test("readabilityScorecard: empty page does not throw and returns degenerate-but-valid scorecard", () => {
  const parsed = parseSections({ html: "" });
  assert.doesNotThrow(() => readabilityScorecard(parsed));
  const scorecard = readabilityScorecard(parsed);
  assert.equal(scorecard.language, "und");
  assert.equal(scorecard.englishDependentMetricsApplicable, false);
  assert.equal(scorecard.ctaInventory.length, 0);
});
