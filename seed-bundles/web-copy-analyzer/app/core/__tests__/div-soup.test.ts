import { test } from "node:test";
import assert from "node:assert/strict";
import { parseSections } from "../html-parser.js";
import { readabilityScorecard } from "../readability.js";

// A realistic "div-soup" landing page: no semantic tags (<header>,
// <section>, <footer>, <h1>) and no class-name hints ("cta", "testimonial",
// "proof", "footer") anywhere — utility-class-only markup as produced by
// most modern component frameworks (React/Vue + Tailwind-style build
// pipelines). This is the exact shape that broke the old tag/class-only
// heuristics on real pages like plausible.io.
const DIV_SOUP_HTML = `<html><body>
  <div class="a1b2">
    <div class="c3d4">
      <a href="/">Home</a>
      <a href="/product">Product</a>
      <a href="/pricing">Pricing</a>
      <a href="/docs">Docs</a>
      <a href="/blog">Blog</a>
      <a href="/about">About</a>
      <a href="/careers">Careers</a>
      <a href="/contact">Contact</a>
    </div>
  </div>
  <div class="e5f6">
    <div class="g7h8">The simplest way to ship your product to millions of happy users</div>
  </div>
  <div class="i9j0">
    <div class="k1l2">Every plan includes unlimited deploys, instant rollbacks, and round-the-clock monitoring so your team never has to babysit a release again, no matter how large the codebase grows.</div>
  </div>
  <div class="m3n4">
    <div class="o5p6">"This tool doubled our activation rate in a single quarter," says Jane Cooper, VP of Marketing at Acme Corp.</div>
  </div>
  <div class="q7r8">
    <div class="s9t0">Trusted by 12,000+ teams worldwide, from scrappy startups to Fortune 500 engineering orgs.</div>
  </div>
  <div class="u1v2">
    <div class="w3x4">Frequently Asked Questions</div>
    <div class="y5z6">Do you support single sign-on? Yes, every paid plan includes SAML-based SSO with no extra configuration required, and our support team can help you set it up in minutes.</div>
  </div>
  <div class="a7b8">
    <div class="c9d0">© 2026 Acme Corp. All rights reserved. Privacy Policy. Terms of Service.</div>
  </div>
</body></html>`;

test("div-soup: mega-menu nav (link-dense boilerplate) is classified `other` and excluded from above-fold content", () => {
  const result = parseSections({ html: DIV_SOUP_HTML });
  const nav = result.sections.find((s) => s.text.includes("Home") && s.text.includes("Careers"));
  assert.ok(nav, "expected the nav link list to appear as a section");
  assert.equal(nav!.role, "other");
  assert.equal(nav!.aboveFoldEstimate, false, "mega-menu must not count as above-fold content");
});

test("div-soup: hero headline (plain div, no h1/class hint) is detected as hero/headline", () => {
  const result = parseSections({ html: DIV_SOUP_HTML });
  const headline = result.sections.find((s) => s.role === "hero" || s.role === "headline");
  assert.ok(headline, `expected a hero/headline section, got roles: ${result.sections.map((s) => s.role).join(",")}`);
  assert.ok(headline!.text.includes("simplest way to ship"));
});

test("div-soup: testimonial + customer-count divs (no class hints) are detected as proof", () => {
  const result = parseSections({ html: DIV_SOUP_HTML });
  const proofSections = result.sections.filter((s) => s.role === "proof");
  assert.ok(proofSections.length >= 2, `expected >=2 proof sections, got: ${JSON.stringify(proofSections)}`);
  assert.ok(proofSections.some((s) => s.text.includes("Jane Cooper")));
  assert.ok(proofSections.some((s) => s.text.includes("12,000+")));
});

test("div-soup: FAQ div (no class hint, but keyword text) is detected as faq", () => {
  const result = parseSections({ html: DIV_SOUP_HTML });
  assert.ok(result.sections.some((s) => s.role === "faq"));
});

test("div-soup: footer div (© + Privacy Policy + Terms, no <footer> tag) is detected as footer", () => {
  const result = parseSections({ html: DIV_SOUP_HTML });
  const footer = result.sections.find((s) => s.role === "footer");
  assert.ok(footer, `expected a footer section, got roles: ${result.sections.map((s) => s.role).join(",")}`);
  assert.ok(footer!.text.includes("©"));
});

test("div-soup: readabilityScorecard reports headline_present/trust_signal_present/footer_present all true", () => {
  const parsed = parseSections({ html: DIV_SOUP_HTML });
  const scorecard = readabilityScorecard(parsed);
  const item = (name: string) => scorecard.structureChecklist.find((c) => c.item === name)?.pass;
  assert.equal(item("headline_present"), true);
  assert.equal(item("trust_signal_present"), true);
  assert.equal(item("footer_present"), true);
});

// --- Precision guard --------------------------------------------------------
// A plain page with plenty of numbers (pricing, feature counts) but NO real
// social-proof signal (no quote+attribution, no star rating, no trust
// phrase) must NOT be tagged `proof` / trust_signal_present=true. This
// guards against over-tagging: the content-based proof fallback requires a
// COMBINATION of signals specifically so that bare numbers (a price, a
// storage limit, a seat count) never trip it on their own.
const NUMBERS_BUT_NO_PROOF_HTML = `<html><body>
  <div class="hero"><div class="headline">Pricing built for teams of any size</div></div>
  <div class="tiers">
    <div class="tier1">Starter plan: $29 per month, up to 5 seats and 100 GB of storage.</div>
    <div class="tier2">Growth plan: $99 per month, up to 25 seats and 500 GB of storage, 3 environments.</div>
    <div class="tier3">Enterprise plan: custom pricing, unlimited seats and 10 TB of storage, 24/7 support.</div>
  </div>
  <div class="footer"><div class="legal">© 2026 Example Inc. All rights reserved. Privacy Policy. Terms of Service.</div></div>
</body></html>`;

test("precision guard: plain page with numbers but no real proof signal is NOT tagged trust_signal_present", () => {
  const parsed = parseSections({ html: NUMBERS_BUT_NO_PROOF_HTML });
  const scorecard = readabilityScorecard(parsed);
  const trustSignal = scorecard.structureChecklist.find((c) => c.item === "trust_signal_present")?.pass;
  assert.equal(trustSignal, false, "bare numbers (price/seats/storage) must not be classified as social proof");
  assert.ok(!parsed.sections.some((s) => s.role === "proof"), "no section should be tagged proof on this fixture");
});
