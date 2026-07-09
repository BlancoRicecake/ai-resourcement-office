/**
 * Growth-layer hygiene rules (design.md §6-3, §6-4, 문제표 #11, §11 설계 원칙).
 *
 * "remember" MUST refuse: customer PII (email / phone / national-id-style
 * numbers) and undisclosed revenue/conversion/traffic actuals (currency or
 * percentage figures near revenue-ish keywords). This module only detects —
 * it never stores anything (§11 "저장 계층에 필드 자체를 두지 않음", i.e.
 * collection prevention happens by refusing before the write, not by storing
 * then redacting).
 */

export interface ForbiddenCheckResult {
  forbidden: boolean;
  reason?: "pii" | "undisclosed_metrics";
}

const EMAIL_RE = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;
// Requires explicit separators (hyphen/dot/space) between digit groups so
// ordinary prose numbers ("40% increase over 90 days") don't false-positive.
const PHONE_RE = /\b(\+?\d{1,3}[-.\s])?\(?\d{2,4}\)?[-.\s]\d{3,4}[-.\s]\d{4}\b/;
const KR_RESIDENT_ID_RE = /\b\d{6}[-\s]?[1-4]\d{6}\b/;

// Currency + revenue-ish keyword within ~10 chars, either order.
const REVENUE_KEYWORDS = "revenue|arr|mrr|매출|수익|영업이익|전환율|conversion rate|conversion|트래픽|traffic";
const CURRENCY = "\\$|₩|€|£|usd|krw|원";
const REVENUE_AFTER_CURRENCY_RE = new RegExp(`(?:${CURRENCY})\\s?[\\d,.]+(?:\\D{0,12})?(?:${REVENUE_KEYWORDS})`, "i");
const REVENUE_BEFORE_CURRENCY_RE = new RegExp(`(?:${REVENUE_KEYWORDS})\\D{0,12}(?:${CURRENCY})\\s?[\\d,.]+`, "i");
// Native Korean digit-then-unit monetary phrasing (e.g. "5000만원", "3억원",
// "500원") — Korean writes the amount BEFORE the currency unit, the opposite
// order of the ₩-branch above (₩5,000,000). Mirrors the same keyword-gating
// as REVENUE_AFTER_CURRENCY_RE / REVENUE_BEFORE_CURRENCY_RE (a REVENUE_KEYWORDS
// term must appear within ~12 chars, either side) so precision stays
// consistent with the ₩-form: a bare amount alone (no revenue-ish keyword
// nearby) is not flagged.
const KRW_NATIVE_AMOUNT = "\\d[\\d,]*\\s?(?:만|억|조)?\\s?원";
const REVENUE_AFTER_KRW_NATIVE_RE = new RegExp(`(?:${KRW_NATIVE_AMOUNT})(?:\\D{0,12})?(?:${REVENUE_KEYWORDS})`, "i");
const REVENUE_BEFORE_KRW_NATIVE_RE = new RegExp(`(?:${REVENUE_KEYWORDS})\\D{0,12}(?:${KRW_NATIVE_AMOUNT})`, "i");
// Bare percentage tied to a conversion/traffic keyword (no currency needed).
const PERCENT_METRIC_RE = new RegExp(`(?:${REVENUE_KEYWORDS})\\D{0,12}\\d+(?:\\.\\d+)?\\s?%|\\d+(?:\\.\\d+)?\\s?%\\D{0,12}(?:${REVENUE_KEYWORDS})`, "i");

export function detectForbiddenContent(text: string): ForbiddenCheckResult {
  if (EMAIL_RE.test(text) || KR_RESIDENT_ID_RE.test(text) || PHONE_RE.test(text)) {
    return { forbidden: true, reason: "pii" };
  }
  if (
    REVENUE_AFTER_CURRENCY_RE.test(text) ||
    REVENUE_BEFORE_CURRENCY_RE.test(text) ||
    REVENUE_AFTER_KRW_NATIVE_RE.test(text) ||
    REVENUE_BEFORE_KRW_NATIVE_RE.test(text) ||
    PERCENT_METRIC_RE.test(text)
  ) {
    return { forbidden: true, reason: "undisclosed_metrics" };
  }
  return { forbidden: false };
}

/** User-facing message for 문제표 #11 (verbatim from the problem table). */
export const FORBIDDEN_MEMORY_MESSAGE = "이 정보(개인정보/미공개 매출)는 기억하지 않습니다.";
