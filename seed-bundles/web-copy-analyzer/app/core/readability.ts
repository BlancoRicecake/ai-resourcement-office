/**
 * readabilityScorecard — deterministic copy metrics (design.md §2-3 #4).
 *
 * Per design.md's MAJOR#4 fix: english_dependent_metrics_applicable gates
 * grade_level / we_you_ratio / jargon_density. Language-neutral metrics
 * (structure_checklist, cta_inventory, headline_length) are always valid.
 * The English-dependent metrics are still computed deterministically (pure
 * function of the text) even when gated off, so the host can decide whether
 * to display them as "reference only" per 문제표 #19 — the flag is the
 * contract, not silent omission.
 */

import { JARGON_TERMS } from "./constants.js";
import { detectLanguage } from "./language.js";
import type { CtaInventoryItem, ParsedPage, Scorecard, StructureChecklistItem } from "./types.js";

function countSyllables(word: string): number {
  const w = word.toLowerCase().replace(/[^a-z]/g, "");
  if (w.length === 0) return 0;
  const groups = w.match(/[aeiouy]+/g);
  let count = groups ? groups.length : 1;
  if (w.endsWith("e") && count > 1) count--;
  return Math.max(count, 1);
}

function splitSentences(text: string): string[] {
  return text
    .split(/[.!?]+(?:\s|$)/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function splitWords(text: string): string[] {
  return text.split(/\s+/).map((w) => w.trim()).filter(Boolean);
}

function countWordBoundary(text: string, pattern: RegExp): number {
  const matches = text.match(pattern);
  return matches ? matches.length : 0;
}

export function readabilityScorecard(parsedPage: ParsedPage): Scorecard {
  const fullText = parsedPage.sections.map((s) => s.text).join(" ").trim();

  const { language, isEnglish } = detectLanguage(fullText);

  const sentences = splitSentences(fullText);
  const words = splitWords(fullText);
  const sentenceCount = Math.max(sentences.length, 1);
  const wordCount = Math.max(words.length, 1);
  const syllableCount = words.reduce((acc, w) => acc + countSyllables(w), 0);

  const avgSentenceLen = words.length / sentenceCount;
  // Flesch-Kincaid Grade Level — an English-calibrated formula; computing it
  // on non-English text produces a meaningless number, hence the gating flag.
  const gradeLevel = 0.39 * (words.length / sentenceCount) + 11.8 * (syllableCount / wordCount) - 15.59;

  const ctaInventory: CtaInventoryItem[] = parsedPage.sections
    .filter((s) => s.role === "cta")
    .map((s) => ({ text: s.text, domIndex: s.domIndex }));

  const headlineSection = parsedPage.sections.find((s) => s.role === "hero" || s.role === "headline");
  const headlineLength = {
    chars: headlineSection?.text.length ?? 0,
    words: headlineSection ? splitWords(headlineSection.text).length : 0,
  };

  const proofPresent = parsedPage.sections.some((s) => s.role === "proof");
  const footerPresent = parsedPage.sections.some((s) => s.role === "footer");

  const structureChecklist: StructureChecklistItem[] = [
    { item: "headline_present", pass: headlineSection !== undefined && headlineSection.text.length > 0 },
    // H4: attention ratio ~1:1 — exactly one primary CTA is the target shape.
    { item: "single_primary_cta", pass: ctaInventory.length === 1 },
    { item: "trust_signal_present", pass: proofPresent },
    { item: "footer_present", pass: footerPresent },
  ];

  const weCount = countWordBoundary(fullText, /\b(we|us|our)\b/gi);
  const youCount = countWordBoundary(fullText, /\b(you|your|yours)\b/gi);
  const weYouRatio = {
    we: weCount,
    you: youCount,
    // Avoid Infinity/NaN in a JSON-serializable output: 0 we-mentions with
    // you-mentions present is reported as youCount (i.e. "all you-language").
    ratio: youCount / (weCount || 1),
  };

  const lowerText = fullText.toLowerCase();
  let jargonTerms = 0;
  for (const term of JARGON_TERMS) {
    const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const re = new RegExp(`\\b${escaped}\\b`, "gi");
    const matches = lowerText.match(re);
    if (matches) jargonTerms += matches.length;
  }
  const jargonDensity = {
    jargonTerms,
    per100Words: (jargonTerms / wordCount) * 100,
  };

  return {
    language,
    englishDependentMetricsApplicable: isEnglish,
    readability: {
      gradeLevel: Number.isFinite(gradeLevel) ? Math.round(gradeLevel * 100) / 100 : 0,
      avgSentenceLen: Math.round(avgSentenceLen * 100) / 100,
    },
    structureChecklist,
    ctaInventory,
    headlineLength,
    weYouRatio,
    jargonDensity,
  };
}
