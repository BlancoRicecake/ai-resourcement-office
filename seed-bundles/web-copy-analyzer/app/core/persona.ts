/**
 * definePersona — pure validation/normalization (design.md §2-2, no side effects).
 *
 * Scope note (design ambiguity resolved): design.md §2-2 lists savePersona /
 * listPersonas / getPersona / deletePersona as core functions with file
 * read/write side effects against the `~/.web-copy-analyzer/` growth layer
 * (§6-1). Per this phase's assignment ("later phases handle
 * adapters/growth/plugin"), growth-layer persistence is out of scope here —
 * only the pure, side-effect-free definePersona (validate + normalize a
 * PersonaDraft into a Persona) is implemented in this phase. Consequently,
 * buildDiagnosisContext / buildRewriteContext in prep-context.ts accept an
 * already-resolved `Persona` object rather than a `persona_id` + file read —
 * the persona_id -> Persona resolution (and 문제표 #8/#9 missing/corrupt-file
 * handling) is a growth-layer adapter concern for a later phase to wire in
 * front of these pure functions.
 */

import { MAX_ID_LEN, MAX_NAME_LEN } from "./constants.js";
import type { Persona, PersonaDraft } from "./types.js";

export class PersonaValidationError extends Error {}

function slugify(name: string): string {
  // Unicode-safe: keep letters (incl. Korean) and digits, collapse everything
  // else (whitespace, punctuation, path chars like / \ .) into a single "-".
  // Korean-first: a Korean-only name must yield a usable id, mirroring the
  // Korean-safe id policy in growth/store.ts assertSafeId. toLowerCase() only
  // affects ASCII; it is a no-op for Korean.
  return name
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "");
}

function normalizeStringArray(values: string[] | undefined): string[] {
  if (!values) return [];
  return values.map((v) => v.trim()).filter((v) => v.length > 0);
}

export function definePersona(draft: PersonaDraft): Persona {
  if (!draft.name || draft.name.trim().length === 0) {
    throw new PersonaValidationError("persona name is required");
  }
  if (draft.name.length > MAX_NAME_LEN) {
    throw new PersonaValidationError(`persona name exceeds ${MAX_NAME_LEN} chars`);
  }
  if (!draft.role || draft.role.trim().length === 0) {
    throw new PersonaValidationError("persona role is required");
  }
  const pains = normalizeStringArray(draft.pains);
  if (pains.length === 0) {
    throw new PersonaValidationError("at least one pain point is required (§2-3 save_persona.attributes.pains)");
  }
  const vocabulary = normalizeStringArray(draft.vocabulary);
  if (vocabulary.length === 0) {
    throw new PersonaValidationError("at least one vocabulary term is required (§2-3 save_persona.attributes.vocabulary)");
  }

  const id = slugify(draft.name);
  if (id.length === 0 || id.length > MAX_ID_LEN) {
    throw new PersonaValidationError("persona name did not produce a usable id");
  }

  return {
    id,
    name: draft.name.trim(),
    role: draft.role.trim(),
    goals: normalizeStringArray(draft.goals),
    pains,
    vocabulary,
    buyingTriggers: normalizeStringArray(draft.buyingTriggers),
  };
}
