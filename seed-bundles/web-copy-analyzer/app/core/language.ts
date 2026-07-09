/**
 * Dependency-free, deterministic language detection.
 *
 * This is intentionally NOT a full NLP language-id model — it is a coarse
 * script + stopword heuristic whose only job is to gate the three
 * English-dependent metrics in readabilityScorecard (design.md §2-3 note,
 * MAJOR#4 fix, 문제표 #19). It must be:
 *   - deterministic (same input -> same output)
 *   - dependency-free (isomorphic core constraint, design.md §4)
 *   - conservative: when unsure, do NOT claim English-applicable.
 */

const ENGLISH_STOPWORDS = [
  "the",
  "and",
  "you",
  "your",
  "for",
  "with",
  "this",
  "that",
  "our",
  "we",
  "is",
  "are",
  "to",
  "of",
  "a",
  "in",
];

/** Returns an ISO 639-1-ish code. "und" (undetermined) is used when no script/heuristic matches. */
export function detectLanguage(text: string): { language: string; isEnglish: boolean } {
  const trimmed = text.trim();
  if (trimmed.length === 0) {
    return { language: "und", isEnglish: false };
  }

  const counts = {
    hangul: 0,
    hiraganaKatakana: 0,
    han: 0,
    cyrillic: 0,
    arabic: 0,
    latin: 0,
  };

  for (const ch of trimmed) {
    const cp = ch.codePointAt(0) ?? 0;
    if (cp >= 0xac00 && cp <= 0xd7a3) counts.hangul++;
    else if ((cp >= 0x3040 && cp <= 0x30ff) || (cp >= 0xff66 && cp <= 0xff9d)) counts.hiraganaKatakana++;
    else if (cp >= 0x4e00 && cp <= 0x9fff) counts.han++;
    else if (cp >= 0x0400 && cp <= 0x04ff) counts.cyrillic++;
    else if (cp >= 0x0600 && cp <= 0x06ff) counts.arabic++;
    else if ((cp >= 0x0041 && cp <= 0x005a) || (cp >= 0x0061 && cp <= 0x007a)) counts.latin++;
  }

  // Script-based detection takes priority (unambiguous, no stopword guessing needed).
  if (counts.hangul > 0 && counts.hangul >= counts.han && counts.hangul >= counts.hiraganaKatakana) {
    return { language: "ko", isEnglish: false };
  }
  if (counts.hiraganaKatakana > 0) {
    return { language: "ja", isEnglish: false };
  }
  if (counts.han > 0) {
    return { language: "zh", isEnglish: false };
  }
  if (counts.cyrillic > 0) {
    return { language: "ru", isEnglish: false };
  }
  if (counts.arabic > 0) {
    return { language: "ar", isEnglish: false };
  }

  // Latin-script text: distinguish English from other Latin-alphabet languages
  // via stopword hit-rate. Conservative threshold — require multiple distinct
  // stopword hits relative to word count before claiming English.
  if (counts.latin === 0) {
    return { language: "und", isEnglish: false };
  }

  const words = trimmed
    .toLowerCase()
    .split(/[^a-z']+/i)
    .filter(Boolean);
  if (words.length === 0) {
    return { language: "und", isEnglish: false };
  }

  const stopwordSet = new Set(ENGLISH_STOPWORDS);
  const stopwordHits = words.filter((w) => stopwordSet.has(w)).length;
  const hitRatio = stopwordHits / words.length;

  // Require a meaningful density of English stopwords, not just presence of
  // Latin letters (e.g. brand names, French/Spanish/German copy also use
  // the Latin script but very different stopwords).
  if (hitRatio >= 0.08 && stopwordHits >= 2) {
    return { language: "en", isEnglish: true };
  }

  return { language: "und", isEnglish: false };
}
