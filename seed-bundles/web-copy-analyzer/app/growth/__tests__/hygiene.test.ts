import { test } from "node:test";
import assert from "node:assert/strict";
import { detectForbiddenContent } from "../hygiene.js";

test("detects email PII", () => {
  assert.equal(detectForbiddenContent("contact jane.doe@company.com for details").forbidden, true);
});

test("detects phone-number-shaped PII", () => {
  assert.equal(detectForbiddenContent("call me at 555-123-4567").forbidden, true);
});

test("detects Korean resident registration number pattern", () => {
  assert.equal(detectForbiddenContent("주민번호 901231-1234567 확인 필요").forbidden, true);
});

test("detects undisclosed revenue figure (currency before keyword)", () => {
  assert.equal(detectForbiddenContent("we hit $50,000 MRR last month").forbidden, true);
});

test("detects undisclosed revenue figure (keyword before currency, Korean)", () => {
  assert.equal(detectForbiddenContent("이번 달 매출 ₩5,000,000 달성").forbidden, true);
});

test("detects conversion-rate percentage tied to a metric keyword", () => {
  assert.equal(detectForbiddenContent("conversion rate jumped to 12.5%").forbidden, true);
});

test("allows ordinary copywriting feedback with numbers", () => {
  const result = detectForbiddenContent("headline is 8 words, above the fold has 3 CTAs, cut jargon by 40%");
  assert.equal(result.forbidden, false);
});

test("allows brand voice / forbidden phrase preferences", () => {
  assert.equal(detectForbiddenContent("brand voice should always use you-language, never 'synergy'").forbidden, false);
});

// Regression: native Korean digit-then-unit revenue phrasing ("5000만원")
// bypassed the guard because the existing regexes only matched the
// currency-symbol-first order (₩5,000,000). See growth/hygiene.ts comment
// above KRW_NATIVE_AMOUNT for the mirrored keyword-gating rule.
test("detects undisclosed revenue figure (native Korean digit-then-unit, 만원)", () => {
  const result = detectForbiddenContent("우리 매출은 월 5000만원입니다.");
  assert.equal(result.forbidden, true);
  assert.equal(result.reason, "undisclosed_metrics");
});

test("detects undisclosed revenue figure (native Korean digit-then-unit, 억원)", () => {
  const result = detectForbiddenContent("연 매출 3억원");
  assert.equal(result.forbidden, true);
  assert.equal(result.reason, "undisclosed_metrics");
});

test("detects undisclosed revenue figure (native Korean digit-then-unit, keyword then amount)", () => {
  const result = detectForbiddenContent("매출 500만원 달성");
  assert.equal(result.forbidden, true);
  assert.equal(result.reason, "undisclosed_metrics");
});

test("still detects the ₩ symbol-first Korean form (regression guard)", () => {
  assert.equal(detectForbiddenContent("MRR ₩5,000,000").forbidden, true);
});

test("still detects email PII alongside Korean copy (regression guard)", () => {
  assert.equal(detectForbiddenContent("문의: jane.doe@company.com 로 연락주세요").forbidden, true);
});

test("a bare Korean amount with no revenue keyword nearby stays allowed", () => {
  const result = detectForbiddenContent("이 상품은 5000원짜리 커피 한 잔 값입니다.");
  assert.equal(result.forbidden, false);
});
