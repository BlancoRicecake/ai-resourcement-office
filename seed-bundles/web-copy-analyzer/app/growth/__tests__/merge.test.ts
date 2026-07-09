import { test } from "node:test";
import assert from "node:assert/strict";
import { mergeInstructions } from "../merge.js";
import type { GrowthSnapshot } from "../types.js";

const AGENTS_MD = "## ④ 주의 케이스\n- 후기 리라이트 금지";

const EMPTY_SNAPSHOT: GrowthSnapshot = { personas: [], brandVoice: [], forbiddenPhrases: [], corrupted: [] };

test("mergeInstructions: empty growth layer returns AGENTS.md unchanged", () => {
  assert.equal(mergeInstructions(AGENTS_MD, EMPTY_SNAPSHOT), AGENTS_MD);
});

test("mergeInstructions: user growth layer is placed before AGENTS.md (user-first, §6-2)", () => {
  const snapshot: GrowthSnapshot = {
    personas: [{ id: "sam", name: "Sam", role: "founder", updatedAt: "" }],
    brandVoice: ["always formal"],
    forbiddenPhrases: ["synergy"],
    corrupted: [],
  };
  const merged = mergeInstructions(AGENTS_MD, snapshot);
  const growthIdx = merged.indexOf("성장 레이어");
  const agentsIdx = merged.indexOf("주의 케이스");
  assert.ok(growthIdx >= 0 && agentsIdx >= 0);
  assert.ok(growthIdx < agentsIdx, "growth section must come before AGENTS.md content");
  assert.match(merged, /always formal/);
  assert.match(merged, /synergy/);
  assert.match(merged, /Sam/);
});

test("mergeInstructions: notes corrupted growth entries without breaking the merge", () => {
  const snapshot: GrowthSnapshot = { ...EMPTY_SNAPSHOT, brandVoice: ["x"], corrupted: ["garbage line"] };
  const merged = mergeInstructions(AGENTS_MD, snapshot);
  assert.match(merged, /1건은 손상되어/);
});
