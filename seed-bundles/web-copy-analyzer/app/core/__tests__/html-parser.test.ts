import { test } from "node:test";
import assert from "node:assert/strict";
import { parseSections } from "../html-parser.js";

const RICH_HTML = `
<html><body>
  <header><h1>Ship faster with Acme Deploy</h1><p>The deploy tool built for teams who hate downtime. Acme Deploy gives every engineering team a single, reliable pipeline from commit to production, with automatic rollbacks and zero-downtime releases baked in from day one. Whether you run a monolith or two hundred microservices, Acme Deploy scales with you, and our on-call engineers can finally stop dreading Friday afternoons because every release ships the same safe, predictable way, every single time, with full audit trails for compliance teams.</p></header>
  <section class="cta"><button class="btn-primary">Start free trial</button></section>
  <section class="testimonial"><p>"Acme cut our deploy time by 80%," says Jane, CTO of Widgets Inc. "We used to dread Fridays. Now we ship on Fridays without a second thought, and our on-call engineers finally get to sleep."</p></section>
  <section class="faq"><h2>Frequently Asked Questions</h2><p>Do you support Kubernetes? Yes, Acme Deploy integrates natively with any Kubernetes cluster, whether self-hosted or managed by a cloud provider, with no extra configuration required.</p></section>
  <footer><p>&copy; 2026 Acme Inc. All rights reserved. Contact our sales team for enterprise pricing and dedicated support options.</p></footer>
</body></html>`;

test("parseSections: rich page produces sections with roles and rich parse_quality", () => {
  const result = parseSections({ html: RICH_HTML });
  assert.ok(result.sections.length > 0);
  assert.equal(result.parseQuality, "rich");
  assert.ok(result.domOrder.length === result.sections.length);
  const roles = result.sections.map((s) => s.role);
  assert.ok(roles.includes("cta"), `expected a cta section, got roles: ${roles.join(",")}`);
  assert.ok(roles.includes("faq"), `expected a faq section, got roles: ${roles.join(",")}`);
});

test("parseSections: entity decoding (&copy; etc.) works", () => {
  const result = parseSections({ html: RICH_HTML });
  const footer = result.sections.find((s) => s.role === "footer");
  assert.ok(footer);
  assert.ok(footer!.text.includes("©"), `expected decoded copyright symbol, got: ${footer!.text}`);
});

test("parseSections: 문제표 #4 — SPA-like page (near-empty body) is classified empty", () => {
  const spaHtml = `<html><body><div id="root"></div><script>renderApp()</script></body></html>`;
  const result = parseSections({ html: spaHtml });
  assert.equal(result.parseQuality, "empty");
  assert.equal(result.sections.length, 0);
});

test("parseSections: 문제표 #4 — sparse page (short text, few sections) classified sparse", () => {
  const sparseHtml = `<html><body><header><h1>Buy Widgets</h1></header><p>Widgets for sale, click below.</p></body></html>`;
  const result = parseSections({ html: sparseHtml });
  assert.notEqual(result.parseQuality, "rich");
});

test("parseSections: 문제표 #6 — malformed/truncated HTML (no closing tags) still returns partial sections without throwing", () => {
  const brokenHtml = `<html><body><header><h1>Incomplete Page Title That Keeps Going`;
  assert.doesNotThrow(() => parseSections({ html: brokenHtml }));
  const result = parseSections({ html: brokenHtml });
  assert.ok(Array.isArray(result.sections));
});

test("parseSections: empty string input returns empty parse_quality, no throw", () => {
  const result = parseSections({ html: "" });
  assert.equal(result.parseQuality, "empty");
  assert.deepEqual(result.sections, []);
});

test("parseSections: 문제표 #18 — mojibake ratio is reported when replacement chars present", () => {
  const mojibakeHtml = `<html><body><header><h1>Bad Encoding</h1><p>������ text with lots of replacement chars ������ that keeps going to avoid sparse classification with more filler words here now and then again and again</p></header></body></html>`;
  const result = parseSections({ html: mojibakeHtml });
  assert.ok(result.mojibakeRatio > 0);
});

test("parseSections: determinism — same input produces identical output", () => {
  const a = parseSections({ html: RICH_HTML });
  const b = parseSections({ html: RICH_HTML });
  assert.deepEqual(a, b);
});

test("parseSections: CTA phrase detection without explicit class hints", () => {
  const html = `<html><body><header><h1>Grow Your Business Today</h1></header><p>We help you grow.</p><a href="/signup">Sign up</a></body></html>`;
  const result = parseSections({ html });
  assert.ok(result.sections.some((s) => s.role === "cta" && s.text.toLowerCase().includes("sign up")));
});

// --- ReDoS / quadratic-parse hardening ---------------------------------------
// Pathological HTML: many repeated *unclosed* <script>/<a> tags. Before the
// fix, SCRIPT_STYLE_RE / the CTA-extraction regex used unbounded lazy
// `[\s\S]*?` spans — an unclosed tag makes each occurrence's failed match
// scan all the way to the end of the string, which is O(n^2) across many
// occurrences. This must now complete quickly on a 200 KB payload of that
// shape (bounded per-occurrence span caps + a hard overall input cap).
test("parseSections: pathological repeated-unclosed-tag HTML parses in bounded time (ReDoS hardening)", () => {
  const chunk = "<script>x".repeat(4000) + "<a href=\"/x\">y".repeat(4000); // ~130 KB, no closing tags
  const pathological = `<html><body>${chunk}</body></html>`;
  assert.ok(pathological.length < 300_000, "fixture must stay under the input cap for this assertion to be meaningful");

  const start = Date.now();
  assert.doesNotThrow(() => parseSections({ html: pathological }));
  const elapsedMs = Date.now() - start;
  assert.ok(elapsedMs < 2000, `expected bounded parse time, took ${elapsedMs}ms`);
});

test("parseSections: input beyond MAX_PARSE_SECTIONS_INPUT_CHARS is truncated and flagged, still completes quickly", () => {
  const huge = "<html><body>" + "<div>a</div>".repeat(100_000) + "</body></html>"; // ~1.2M chars, well over the cap
  const start = Date.now();
  const result = parseSections({ html: huge });
  const elapsedMs = Date.now() - start;
  assert.equal(result.truncated, true);
  assert.ok(elapsedMs < 2000, `expected bounded parse time on oversized input, took ${elapsedMs}ms`);
});
