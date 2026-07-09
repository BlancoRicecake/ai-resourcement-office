import { test } from "node:test";
import assert from "node:assert/strict";
import { definePersona, PersonaValidationError } from "../persona.js";

const VALID_DRAFT = {
  name: "Solo Founder Sam",
  role: "1인 창업자 / 인디해커",
  goals: ["ship a profitable side project"],
  pains: ["no time to write copy", "not a professional marketer"],
  vocabulary: ["MRR", "ship it", "side project"],
  buyingTriggers: ["clear ROI", "quick setup"],
};

test("definePersona: valid draft normalizes into a Persona with slug id", () => {
  const persona = definePersona(VALID_DRAFT);
  assert.equal(persona.id, "solo-founder-sam");
  assert.equal(persona.name, "Solo Founder Sam");
  assert.deepEqual(persona.pains, VALID_DRAFT.pains);
  assert.deepEqual(persona.vocabulary, VALID_DRAFT.vocabulary);
});

test("definePersona: Korean-only name yields a usable Korean id (Korean-first)", () => {
  const persona = definePersona({ ...VALID_DRAFT, name: "부트스트랩 창업자" });
  assert.equal(persona.id, "부트스트랩-창업자");
  assert.equal(persona.name, "부트스트랩 창업자");
  // path-traversal chars must never survive slugify into an id
  const traversal = definePersona({ ...VALID_DRAFT, name: "../../40대 직장맘" });
  assert.equal(traversal.id, "40대-직장맘");
  assert.ok(!/[/\\]|\.\./.test(traversal.id));
});

test("definePersona: trims whitespace and drops empty array entries", () => {
  const persona = definePersona({
    ...VALID_DRAFT,
    pains: ["  real pain  ", "", "   "],
    vocabulary: [" jargon ", ""],
  });
  assert.deepEqual(persona.pains, ["real pain"]);
  assert.deepEqual(persona.vocabulary, ["jargon"]);
});

test("definePersona: rejects missing name", () => {
  assert.throws(() => definePersona({ ...VALID_DRAFT, name: "" }), PersonaValidationError);
});

test("definePersona: rejects missing role", () => {
  assert.throws(() => definePersona({ ...VALID_DRAFT, role: "" }), PersonaValidationError);
});

test("definePersona: rejects empty pains (§2-3 save_persona.attributes requires pains)", () => {
  assert.throws(() => definePersona({ ...VALID_DRAFT, pains: [] }), PersonaValidationError);
});

test("definePersona: rejects empty vocabulary (§2-3 save_persona.attributes requires vocabulary)", () => {
  assert.throws(() => definePersona({ ...VALID_DRAFT, vocabulary: [] }), PersonaValidationError);
});

test("definePersona: rejects name exceeding the 80-char schema cap", () => {
  assert.throws(() => definePersona({ ...VALID_DRAFT, name: "x".repeat(81) }), PersonaValidationError);
});

test("definePersona: determinism — same draft produces identical Persona", () => {
  const a = definePersona(VALID_DRAFT);
  const b = definePersona(VALID_DRAFT);
  assert.deepEqual(a, b);
});
