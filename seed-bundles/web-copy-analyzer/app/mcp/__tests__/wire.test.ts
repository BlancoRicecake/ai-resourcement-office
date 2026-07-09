import { test } from "node:test";
import assert from "node:assert/strict";
import { toCamelDeep, toSnakeDeep } from "../wire.js";

test("toCamelDeep: converts nested snake_case keys recursively, values untouched", () => {
  const wire = {
    parsed_page: {
      sections: [{ id: "s1", dom_index: 3, above_fold_estimate: true, role: "hero" }],
      dom_order: ["s1"],
      parse_quality: "rich",
    },
    persona_id: "sam",
    scope: "above_fold",
  };
  const camel = toCamelDeep<Record<string, unknown>>(wire);
  assert.deepEqual(camel, {
    parsedPage: {
      sections: [{ id: "s1", domIndex: 3, aboveFoldEstimate: true, role: "hero" }],
      domOrder: ["s1"],
      parseQuality: "rich",
    },
    personaId: "sam",
    scope: "above_fold", // enum VALUE, not a key — must stay untouched
  });
});

test("toSnakeDeep: converts nested camelCase keys recursively, round-trips toCamelDeep", () => {
  const core = {
    briefKind: "diagnosis",
    attributionFrame: ["clarity", "trust"],
    deterministicSignals: { textLength: 42 },
  };
  const wire = toSnakeDeep<Record<string, unknown>>(core);
  assert.deepEqual(wire, {
    brief_kind: "diagnosis",
    attribution_frame: ["clarity", "trust"],
    deterministic_signals: { text_length: 42 },
  });
  assert.deepEqual(toCamelDeep(wire), core);
});

test("toSnakeDeep: handles the per_100_words / dom_index style digit-adjacent keys", () => {
  const core = { jargonDensity: { jargonTerms: 2, per100Words: 1.5 } };
  assert.deepEqual(toSnakeDeep(core), { jargon_density: { jargon_terms: 2, per_100_words: 1.5 } });
});
