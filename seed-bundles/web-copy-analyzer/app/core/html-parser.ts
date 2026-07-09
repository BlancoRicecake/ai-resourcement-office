/**
 * parseSections — dependency-free, isomorphic HTML section parser.
 *
 * Design ambiguity resolved here (documented per orchestrator instructions):
 * design.md §4 compares cheerio/parse5/linkedom as the HTML-parsing
 * ecosystem, but all three either pull in a real DOM implementation or add
 * a non-trivial dependency tree. Since 원칙① requires near-zero runtime
 * deps and 원칙② requires the core to run unmodified in Node AND the
 * browser, this file implements a small dependency-free tag tokenizer
 * instead of adopting a parsing library. It is not a general HTML/DOM
 * parser — it only extracts enough structure (heading/CTA/proof/faq
 * boundaries + text) to support §2-2's deterministic scoring contract.
 * A later phase may swap this for linkedom behind the same function
 * signature if richer DOM semantics are needed; callers are unaffected.
 */

import {
  CTA_KEYWORD_HINTS,
  CTA_MAX_SPAN,
  CTA_PHRASES,
  FAQ_KEYWORD_HINTS,
  MAX_PARSE_SECTIONS_INPUT_CHARS,
  PARSE_QUALITY_EMPTY_CHAR_THRESHOLD,
  PARSE_QUALITY_EMPTY_SECTION_THRESHOLD,
  PARSE_QUALITY_SPARSE_CHAR_THRESHOLD,
  PARSE_QUALITY_SPARSE_SECTION_THRESHOLD,
  PROOF_KEYWORD_HINTS,
  SCRIPT_STYLE_MAX_SPAN,
} from "./constants.js";
import type { ParsedPage, ParseQuality, Section, SectionRole } from "./types.js";

// `div` is included deliberately (not just the semantic tags): modern
// div-soup landing pages (no <section>/<footer>/<h1> markup at all past the
// very first heading) otherwise never produce a boundary between the hero,
// a mega-menu, testimonial cards, pricing tiers and the footer — all of that
// text collapses into one giant blob keyed off whichever semantic tag last
// appeared, and a single CTA phrase anywhere in that blob (e.g. "Start free
// trial" inside a pricing div) mislabels the *entire* blob (headline
// included) as `cta`. Splitting on every <div> open tag fragments the page
// into much smaller, independently-classifiable chunks; the content-shape
// heuristics below (proof/footer/nav-boilerplate) then resolve each
// fragment's role without relying on class names or semantic tags.
const BOUNDARY_TAGS = ["header", "nav", "section", "article", "footer", "aside", "form", "div", "h1", "h2", "h3"];
const BOUNDARY_RE = new RegExp(`(<(?:${BOUNDARY_TAGS.join("|")})\\b[^>]*>)`, "gi");
const TAG_RE = /<[^>]*>/g;
// Bounded lazy spans (문제표 ReDoS hardening): an unclosed <script>/<style> tag
// in attacker HTML otherwise makes the lazy `[\s\S]*?` scan all the way to
// the end of the string before giving up on that occurrence — repeated
// across many unclosed tags this is O(n^2). Capping the span means each
// occurrence costs at most O(cap), keeping total work linear in input size.
const SCRIPT_STYLE_RE = new RegExp(`<(script|style)\\b[^>]*>[\\s\\S]{0,${SCRIPT_STYLE_MAX_SPAN}}?<\\/\\1>`, "gi");
const COMMENT_RE = /<!--[\s\S]*?-->/g;

const ENTITY_MAP: Record<string, string> = {
  amp: "&",
  lt: "<",
  gt: ">",
  quot: '"',
  apos: "'",
  nbsp: " ",
  mdash: "—",
  ndash: "–",
  rsquo: "’",
  lsquo: "‘",
  rdquo: "”",
  ldquo: "“",
  copy: "©",
  reg: "®",
  trade: "™",
};

function decodeEntities(text: string): string {
  return text.replace(/&(#x?[0-9a-fA-F]+|[a-zA-Z]+);/g, (match, code: string) => {
    if (code[0] === "#") {
      const isHex = code[1] === "x" || code[1] === "X";
      const num = isHex ? parseInt(code.slice(2), 16) : parseInt(code.slice(1), 10);
      if (Number.isFinite(num)) {
        try {
          return String.fromCodePoint(num);
        } catch {
          return match;
        }
      }
      return match;
    }
    return ENTITY_MAP[code] ?? match;
  });
}

function stripTags(html: string): string {
  return decodeEntities(html.replace(TAG_RE, " "))
    .replace(/\s+/g, " ")
    .trim();
}

function extractTagName(openTag: string): string {
  const m = /^<\s*([a-zA-Z0-9]+)/.exec(openTag);
  return (m?.[1] ?? "").toLowerCase();
}

function containsAny(haystack: string, needles: readonly string[]): boolean {
  const lower = haystack.toLowerCase();
  return needles.some((n) => lower.includes(n));
}

// --- Nav / mega-menu exclusion --------------------------------------------
// Rationale: a primary nav or footer link-column rendered as a plain <div>
// (no <nav> tag, no class hint) is otherwise indistinguishable from a real
// content section — until you look at its *shape*. Boilerplate link lists
// pack many anchors into a small amount of visible text ("Pricing", "Docs",
// "Blog", "About", "Careers", ...). Threshold: >=NAV_MIN_LINK_COUNT anchors
// AND fewer than NAV_MAX_AVG_LINK_TEXT_CHARS characters of visible text per
// anchor on average. A feature grid or hero with a couple of inline links
// essentially never reaches 6+ anchors; a menu/footer nav column reliably
// does. Keeping both conditions (count AND density) avoids misclassifying a
// long prose section that merely happens to contain several links.
const NAV_MIN_LINK_COUNT = 6;
const NAV_MAX_AVG_LINK_TEXT_CHARS = 25;

function isLinkDenseBoilerplate(rawSectionHtml: string, text: string): boolean {
  const anchorCount = (rawSectionHtml.match(/<a\b/gi) ?? []).length;
  if (anchorCount < NAV_MIN_LINK_COUNT) return false;
  return text.length / anchorCount < NAV_MAX_AVG_LINK_TEXT_CHARS;
}

// --- Content-based social-proof fallback (div-soup pages) -----------------
// Rationale: PROOF_KEYWORD_HINTS only fires when the markup literally
// contains a word like "testimonial" or "trusted" (in a class or in the
// copy). Real proof sections on modern sites usually don't — they *read*
// like proof instead. Any single signal below is too weak on its own (a
// pricing page has numbers; an About page quotes a person; a nav has the
// word "reviews" in a link) so a section only qualifies as `proof` on a
// COMBINATION:
//   (a) a substantial quoted phrase co-occurring with a "name — role/company"
//       attribution: an actual testimonial quote.
//   (b) a star/numeric rating glyph ("4.9/5", "★★★★★") together with either
//       a quote or an explicit trust phrase.
//   (c) an explicit trust phrase ("trusted by", "loved by", "used by",
//       "customers", "subscribers", "reviews", ...) together with a
//       quantity token ("19k", "260B", "10,000+") — trust phrase alone is
//       too easy to trip on incidental copy ("read our reviews" nav link);
//       a bare number alone is too easy to trip on a price or stat.
const SOCIAL_PROOF_QUOTE_RE = /["“][^"”]{20,400}["”]/;
const SOCIAL_PROOF_ATTRIBUTION_RE =
  /[,–—-]\s*(CEO|CTO|COO|CMO|CFO|VP|Founder|Co-founder|Cofounder|President|Director|Manager|Head of|Lead)\b/i;
const SOCIAL_PROOF_STAR_RATING_RE = /★{2,}|⭐{2,}|\b\d(?:\.\d)?\s*\/\s*5\b|\b\d(?:\.\d)?\s*(?:out of\s*5|stars?)\b/i;
const SOCIAL_PROOF_TRUST_PHRASE_RE =
  /\b(trusted by|loved by|used by|rated by|reviews from|customers|subscribers|users worldwide|teams (?:use|trust)|companies (?:use|trust))\b/i;
const SOCIAL_PROOF_QUANTITY_RE = /\b\d[\d,]*(?:\.\d+)?\s*[kKmMbB]?\+?/;

function hasSocialProofSignal(text: string): boolean {
  const hasQuote = SOCIAL_PROOF_QUOTE_RE.test(text);
  const hasAttribution = SOCIAL_PROOF_ATTRIBUTION_RE.test(text);
  const hasStarRating = SOCIAL_PROOF_STAR_RATING_RE.test(text);
  const hasTrustPhrase = SOCIAL_PROOF_TRUST_PHRASE_RE.test(text);
  const hasQuantityToken = SOCIAL_PROOF_QUANTITY_RE.test(text);

  if (hasQuote && hasAttribution) return true;
  if (hasStarRating && (hasQuote || hasTrustPhrase)) return true;
  if (hasTrustPhrase && hasQuantityToken) return true;
  return false;
}

function inferRole(tag: string, openTagRaw: string, text: string, domIndex: number, rawSectionHtml: string): SectionRole {
  // footer/nav are structural regions, not content regions: an explicit
  // class hint (e.g. class="cta") still overrides them, but incidental CTA
  // *phrases* in footer/nav boilerplate ("contact us" in a copyright line)
  // must not reclassify the whole boundary section as a primary CTA.
  const isStructuralTag = tag === "footer" || tag === "nav";
  const attrHay = openTagRaw + " " + text.slice(0, 200);

  // Boilerplate link lists (mega-menu, footer nav column) must be excluded
  // *before* any keyword/phrase check runs — otherwise an incidental
  // "Sign up" or "Contact us" list item promotes the entire menu to `cta`.
  if (!isStructuralTag && isLinkDenseBoilerplate(rawSectionHtml, text)) return "other";

  if (containsAny(attrHay, CTA_KEYWORD_HINTS) || (!isStructuralTag && containsAny(text, CTA_PHRASES))) return "cta";
  if (containsAny(attrHay, FAQ_KEYWORD_HINTS)) return "faq";
  if (containsAny(attrHay, PROOF_KEYWORD_HINTS)) return "proof";
  if (tag === "footer") return "footer";
  if (tag === "nav") return "other";
  if (tag === "header") return domIndex === 0 ? "hero" : "headline";
  if (tag === "h1") return domIndex === 0 ? "hero" : "headline";
  if (tag === "h2" || tag === "h3") return "subhead";
  // Content-based proof fallback: restricted to generic content containers
  // (never headings) so a hero headline that happens to mention a number
  // can't be re-tagged `proof`.
  if ((tag === "div" || tag === "section" || tag === "article" || tag === "aside" || tag === "form") && hasSocialProofSignal(text)) {
    return "proof";
  }
  if (tag === "section" || tag === "article" || tag === "aside" || tag === "form") return "feature";
  return "other";
}

function extractBody(html: string): string {
  const bodyMatch = /<body\b[^>]*>([\s\S]*?)(<\/body>|$)/i.exec(html);
  if (bodyMatch?.[1] !== undefined) return bodyMatch[1];
  // No <body> tag at all (or unclosed) — 문제표 #6: fall back to whatever we have,
  // stripping <html>/<head> wrapper tags if present, so partial parsing can proceed.
  return html;
}

function extractCtaCandidates(bodyHtml: string, startIndex: number): Array<{ text: string; index: number }> {
  const results: Array<{ text: string; index: number }> = [];
  // Bounded lazy span — see SCRIPT_STYLE_RE comment above; same ReDoS class
  // via repeated unclosed <button>/<a> tags.
  const re = new RegExp(`<(button|a)\\b([^>]*)>([\\s\\S]{0,${CTA_MAX_SPAN}}?)<\\/\\1>`, "gi");
  let m: RegExpExecArray | null;
  let idx = startIndex;
  while ((m = re.exec(bodyHtml)) !== null) {
    const attrs = m[2] ?? "";
    const inner = stripTags(m[3] ?? "");
    if (!inner) continue;
    if (containsAny(attrs, CTA_KEYWORD_HINTS) || containsAny(inner, CTA_PHRASES)) {
      results.push({ text: inner, index: idx });
      idx++;
    }
  }
  return results;
}

export function parseSections(input: { html: string; baseUrl?: string }): ParsedPage {
  const rawInput = input.html ?? "";
  // Hard cap the input length up front (ReDoS/quadratic-blowup hardening):
  // bounds total parse work regardless of tag density, independent of the
  // per-occurrence span caps above. `truncate 후 진행` — same posture as
  // fetch-node.ts's max_bytes truncation (design.md §5 문제표 #5).
  const inputTruncated = rawInput.length > MAX_PARSE_SECTIONS_INPUT_CHARS;
  const rawHtml = inputTruncated ? rawInput.slice(0, MAX_PARSE_SECTIONS_INPUT_CHARS) : rawInput;

  // 문제표 #18: mojibake ratio measured on the raw input text (decode-time
  // mismatches surface as U+FFFD before this function ever sees the string;
  // fetch-node.ts is responsible for the decode step itself).
  const replacementCount = (rawHtml.match(/�/g) ?? []).length;
  const mojibakeRatio = rawHtml.length > 0 ? replacementCount / rawHtml.length : 0;

  const cleaned = rawHtml.replace(SCRIPT_STYLE_RE, " ").replace(COMMENT_RE, " ");
  const bodyHtml = extractBody(cleaned);

  const fullBodyText = stripTags(bodyHtml);

  const parts = bodyHtml.split(BOUNDARY_RE);
  const sections: Section[] = [];
  let domIndex = 0;
  let currentTag: string | null = null;
  let currentOpenTagRaw = "";
  let currentTextChunks: string[] = [];
  let cumulativeCharOffset = 0;
  const aboveFoldCharBudget = Math.max(fullBodyText.length * 0.25, 600);

  const flush = () => {
    if (currentTag === null) return;
    const rawSectionHtml = currentTextChunks.join(" ");
    const text = stripTags(rawSectionHtml);
    if (text.length > 0) {
      const role = inferRole(currentTag, currentOpenTagRaw, text, domIndex, rawSectionHtml);
      // Boilerplate nav/mega-menu sections are excluded from the above-fold
      // CONTENT budget too: otherwise a link-dense menu rendered early in
      // the DOM (the common case) eats most of the aboveFoldCharBudget
      // before the real hero/headline text is even reached, pushing
      // legitimate content out of the "above the fold" window it actually
      // occupies visually.
      const isBoilerplate = role === "other" && isLinkDenseBoilerplate(rawSectionHtml, text);
      sections.push({
        id: `s${domIndex}`,
        role,
        text,
        domIndex,
        aboveFoldEstimate: !isBoilerplate && cumulativeCharOffset <= aboveFoldCharBudget,
      });
      if (!isBoilerplate) cumulativeCharOffset += text.length;
      domIndex++;
    }
    currentTextChunks = [];
  };

  for (const part of parts) {
    if (BOUNDARY_RE.test(part)) {
      BOUNDARY_RE.lastIndex = 0; // stateful global regex guard
      flush();
      currentTag = extractTagName(part);
      currentOpenTagRaw = part;
    } else {
      currentTextChunks.push(part);
    }
  }
  flush();

  // --- Headline/hero fallback (div-soup pages with no <h1>/<header>) ------
  // H2: every landing page has *a* prominent early value-prop headline. If
  // no semantic tag produced a hero/headline role, promote the earliest
  // above-fold, non-boilerplate content section that reads like a short
  // headline (H2 target ~10 words; HEADLINE_MAX_WORDS gives slack for
  // multi-clause value props) rather than a full paragraph. If nothing that
  // short exists above the fold, fall back to the very first above-fold
  // content section — an imperfect headline signal beats none at all.
  const HEADLINE_MAX_WORDS = 16;
  if (!sections.some((s) => s.role === "hero" || s.role === "headline")) {
    const aboveFoldContent = sections.filter(
      (s) => s.aboveFoldEstimate && s.role !== "footer" && s.role !== "cta" && s.role !== "faq" && s.role !== "proof",
    );
    const short = aboveFoldContent.find((s) => s.text.split(/\s+/).filter(Boolean).length <= HEADLINE_MAX_WORDS);
    const promoted = short ?? aboveFoldContent[0];
    if (promoted) promoted.role = "hero";
  }

  // --- Footer fallback (div-soup pages with no <footer> tag) --------------
  // Rationale: footers are identified by combining POSITION (always the
  // last major region) with CONTENT (copyright/legal boilerplate). Either
  // alone is unreliable — a "Privacy Policy" link can appear in a header
  // disclaimer; the literal last <div> is sometimes just a script-mount
  // wrapper with no legal text. Requiring both, restricted to the tail
  // FOOTER_POSITION_TAIL_RATIO of parsed sections (or the final two,
  // whichever window is larger), keeps precision high.
  const FOOTER_CONTENT_HINTS = [
    "©",
    "copyright",
    "all rights reserved",
    "privacy policy",
    "terms of service",
    "terms & conditions",
    "terms and conditions",
  ];
  const FOOTER_POSITION_TAIL_RATIO = 0.85;
  if (sections.length > 0 && !sections.some((s) => s.role === "footer")) {
    const tailStart = Math.min(
      Math.max(sections.length - 2, 0),
      Math.floor(sections.length * FOOTER_POSITION_TAIL_RATIO),
    );
    for (let i = tailStart; i < sections.length; i++) {
      const s = sections[i];
      if (s === undefined) continue;
      if (s.role === "hero" || s.role === "headline" || s.role === "cta" || s.role === "proof" || s.role === "faq") continue;
      if (containsAny(s.text, FOOTER_CONTENT_HINTS)) {
        s.role = "footer";
        break;
      }
    }
  }

  // Supplementary CTA pass: standalone <button>/<a> elements are frequently
  // *inside* a boundary section (e.g. a hero) and would otherwise be buried
  // in that section's text rather than surfaced individually for the CTA
  // inventory / attention-ratio checks (H4). Skip candidates whose text is
  // already captured verbatim by an existing boundary-derived `cta` section
  // (e.g. `<section class="cta"><button>Start</button></section>`) to avoid
  // double-counting the same call-to-action for the attention-ratio check.
  const existingCtaTexts = new Set(sections.filter((s) => s.role === "cta").map((s) => s.text));
  const ctaCandidates = extractCtaCandidates(bodyHtml, domIndex);
  for (const cta of ctaCandidates) {
    if (existingCtaTexts.has(cta.text)) continue;
    sections.push({
      id: `s${cta.index}`,
      role: "cta",
      text: cta.text,
      domIndex: cta.index,
      aboveFoldEstimate: cumulativeCharOffset <= aboveFoldCharBudget,
    });
    existingCtaTexts.add(cta.text);
  }

  const domOrder = sections.map((s) => s.id);

  const totalChars = fullBodyText.length;
  const sectionCount = sections.length;
  let parseQuality: ParseQuality;
  if (totalChars < PARSE_QUALITY_EMPTY_CHAR_THRESHOLD || sectionCount <= PARSE_QUALITY_EMPTY_SECTION_THRESHOLD) {
    parseQuality = "empty";
  } else if (totalChars < PARSE_QUALITY_SPARSE_CHAR_THRESHOLD || sectionCount <= PARSE_QUALITY_SPARSE_SECTION_THRESHOLD) {
    parseQuality = "sparse";
  } else {
    parseQuality = "rich";
  }

  return { sections, domOrder, parseQuality, mojibakeRatio, ...(inputTruncated ? { truncated: true } : {}) };
}
