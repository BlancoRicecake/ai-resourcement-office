import { test } from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { GrowthStore } from "../store.js";
import { PersonaCorruptError, PersonaNameCollisionError, PersonaNotFoundError } from "../types.js";
import { PersonaValidationError } from "../../core/persona.js";

const VALID_DRAFT = {
  name: "Solo Founder Sam",
  role: "1인 창업자",
  goals: ["ship a profitable side project"],
  pains: ["no time to write copy"],
  vocabulary: ["MRR", "ship it"],
  buyingTriggers: ["clear ROI"],
};

async function tmpRoot(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), "wca-growth-"));
}

test("savePersona/getPersona/listPersonas/deletePersona round-trip (never touches real home)", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });

  const saved = await store.savePersona({ draft: VALID_DRAFT });
  assert.equal(saved.saved, true);
  assert.equal(saved.id, "solo-founder-sam");
  assert.ok(saved.path.startsWith(rootDir));

  const list = await store.listPersonas();
  assert.equal(list.length, 1);
  assert.equal(list[0]?.id, "solo-founder-sam");

  const fetched = await store.getPersona("solo-founder-sam");
  assert.equal(fetched.name, "Solo Founder Sam");
  assert.deepEqual(fetched.pains, VALID_DRAFT.pains);

  const del = await store.deletePersona("solo-founder-sam");
  assert.equal(del.deleted, true);
  assert.equal((await store.listPersonas()).length, 0);
});

test("문제표 #22: save_persona same slug + overwrite=false throws PersonaNameCollisionError, does not clobber", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  await store.savePersona({ draft: VALID_DRAFT });

  await assert.rejects(
    () => store.savePersona({ draft: { ...VALID_DRAFT, role: "changed role" } }),
    PersonaNameCollisionError
  );

  const persona = await store.getPersona("solo-founder-sam");
  assert.equal(persona.role, "1인 창업자"); // untouched

  const overwritten = await store.savePersona({ draft: { ...VALID_DRAFT, role: "changed role" }, overwrite: true });
  assert.equal(overwritten.saved, true);
  const after = await store.getPersona("solo-founder-sam");
  assert.equal(after.role, "changed role");
});

test("문제표 #8: get_persona for missing id throws PersonaNotFoundError with available list", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  await store.savePersona({ draft: VALID_DRAFT });

  await assert.rejects(
    () => store.getPersona("does-not-exist"),
    (err: unknown) => {
      assert.ok(err instanceof PersonaNotFoundError);
      assert.deepEqual(err.available, ["solo-founder-sam"]);
      assert.match(err.message, /solo-founder-sam/);
      return true;
    }
  );
});

test("문제표 #9: corrupt persona file is isolated — listPersonas skips it, other personas still load", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  await store.savePersona({ draft: VALID_DRAFT });
  await store.savePersona({ draft: { ...VALID_DRAFT, name: "Second Persona" } });

  const personasDir = path.join(rootDir, "personas");
  await fs.writeFile(path.join(personasDir, "corrupt.md"), "not frontmatter at all\nrandom garbage", "utf-8");

  const list = await store.listPersonas();
  assert.equal(list.length, 2);
  assert.ok(!list.some((p) => p.id === "corrupt"));

  await assert.rejects(() => store.getPersona("corrupt"), PersonaCorruptError);
});

test("persona id path traversal is rejected (§5)", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  await assert.rejects(() => store.getPersona("../../etc/passwd"));
});

test("remember: 문제표 #11 rejects PII (email) with the exact hygiene message, does not store", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  const result = await store.remember({ kind: "decision", content: "customer email is jane@example.com" });
  assert.equal(result.stored, false);
  assert.equal(result.rejected, true);
  assert.equal(result.shown, "이 정보(개인정보/미공개 매출)는 기억하지 않습니다.");

  const raw = await fs.readFile(path.join(rootDir, "decisions.log"), "utf-8").catch(() => "");
  assert.doesNotMatch(raw, /jane@example\.com/);
});

test("remember: 문제표 #11 rejects undisclosed revenue figures", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  const result = await store.remember({ kind: "decision", content: "our ARR is $1.2M this quarter" });
  assert.equal(result.stored, false);
  assert.equal(result.rejected, true);
});

test("remember: allowed content is stored and displayed (원칙7 — must show what was remembered)", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  const result = await store.remember({ kind: "brand_voice", content: "always use formal 존댓말" });
  assert.equal(result.stored, true);
  assert.match(result.shown, /always use formal 존댓말/);

  const snapshot = await store.buildGrowthSnapshot();
  assert.deepEqual(snapshot.brandVoice, ["always use formal 존댓말"]);
});

test("remember: dedup — identical normalized content updates in place instead of duplicating (§6-4)", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  await store.remember({ kind: "forbidden_phrase", content: "  Synergy  " });
  await store.remember({ kind: "forbidden_phrase", content: "synergy" });

  const snapshot = await store.buildGrowthSnapshot();
  assert.equal(snapshot.forbiddenPhrases.length, 1);
});

test("schema_version present in persona files and voice/decisions logs", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  await store.savePersona({ draft: VALID_DRAFT });
  await store.remember({ kind: "brand_voice", content: "friendly tone" });

  const personaRaw = await fs.readFile(path.join(rootDir, "personas", "solo-founder-sam.md"), "utf-8");
  assert.match(personaRaw, /schema_version: 1/);

  const voiceRaw = await fs.readFile(path.join(rootDir, "voice.md"), "utf-8");
  assert.match(voiceRaw, /^schema_version:1/);
});

test("saveWorkflow round-trips and is listed by name", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  const result = await store.saveWorkflow({ name: "full-audit", steps: ["fetch_page", "parse_sections", "readability_scorecard"] });
  assert.equal(result.saved, true);
  const names = await store.listWorkflowNames();
  assert.deepEqual(names, ["full-audit"]);
});

test("saveWorkflow accepts a free-form Korean/spaced display name (design §1-A #17 '{이름}' example) and round-trips", async () => {
  // Regression guard: the path-traversal hardening must NOT reject the Korean
  // names the design's own example implies. assertSafeId allows internal
  // spaces + Unicode; it only blocks / \\ .. and untrimmed input.
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  const result = await store.saveWorkflow({ name: "전체 카피 진단", steps: ["fetch_page", "parse_sections"] });
  assert.equal(result.saved, true);
  const names = await store.listWorkflowNames();
  assert.deepEqual(names, ["전체 카피 진단"]);
});

test("saveWorkflow rejects a path-traversal name (../../../../tmp/pwned) and writes no file outside the growth root", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });

  await assert.rejects(
    () => store.saveWorkflow({ name: "../../../../tmp/pwned", steps: ["fetch_page"] }),
    PersonaValidationError
  );

  // No file escaped the growth root.
  await assert.rejects(() => fs.stat("/tmp/pwned.json"));
  // Nothing was written inside the growth root either (rejected before any write).
  await assert.rejects(() => fs.stat(path.join(rootDir, "workflows")));
});

test("saveWorkflow rejects a slug containing a path separator (a/b)", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });

  await assert.rejects(() => store.saveWorkflow({ name: "a/b", steps: ["fetch_page"] }), PersonaValidationError);
});

test("growth files are written with mode 0o600 and the growth dir with 0o700 (multi-user host hardening)", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  await store.savePersona({ draft: VALID_DRAFT });

  const personasDirStat = await fs.stat(path.join(rootDir, "personas"));
  assert.equal(personasDirStat.mode & 0o777, 0o700);

  const fileStat = await fs.stat(path.join(rootDir, "personas", "solo-founder-sam.md"));
  assert.equal(fileStat.mode & 0o777, 0o600);
});

test("concurrent remember() calls with distinct content all persist (문제표 #21 atomic append)", async () => {
  const rootDir = await tmpRoot();
  const store = new GrowthStore({ rootDir });
  const N = 25;
  await Promise.all(
    Array.from({ length: N }, (_, i) => store.remember({ kind: "decision", content: `decision number ${i} adopted` }))
  );

  const snapshot = await store.buildGrowthSnapshot();
  // decisions aren't in the snapshot (voice-only); read decisions.log directly.
  const raw = await fs.readFile(path.join(rootDir, "decisions.log"), "utf-8");
  const lines = raw.split("\n").filter((l) => l.trim().length > 0 && !l.startsWith("schema_version"));
  assert.equal(lines.length, N);
  assert.equal(snapshot.corrupted.length, 0);
});

test("문제표 #20: write failure to an unwritable growth root falls back to session-only, still readable", async () => {
  const rootDir = await tmpRoot();
  // Make the root read-only so mkdir/writeFile under it fails with EACCES.
  await fs.chmod(rootDir, 0o500);
  const store = new GrowthStore({ rootDir });

  let result;
  try {
    result = await store.savePersona({ draft: VALID_DRAFT });
  } finally {
    await fs.chmod(rootDir, 0o700); // restore so tmpdir cleanup works
  }

  assert.equal(result.saved, true);
  assert.equal(result.sessionOnly, true);
  assert.match(result.warning ?? "", /설정 저장 공간에 쓸 수 없습니다/);

  // Still readable within the same session (in-memory fallback).
  const persona = await store.getPersona("solo-founder-sam");
  assert.equal(persona.name, "Solo Founder Sam");
});

test("문제표 #20: buildGrowthSnapshot degrades to an empty snapshot (with warning) when voice.md is unreadable, instead of throwing", async () => {
  const rootDir = await tmpRoot();
  const voicePath = path.join(rootDir, "voice.md");
  await fs.writeFile(voicePath, "schema_version:1\n{\"schemaVersion\":1,\"kind\":\"brand_voice\",\"content\":\"friendly\",\"ts\":\"2024-01-01T00:00:00.000Z\"}\n", "utf-8");
  await fs.chmod(voicePath, 0o000);

  const store = new GrowthStore({ rootDir });
  let snapshot;
  try {
    snapshot = await store.buildGrowthSnapshot();
  } finally {
    await fs.chmod(voicePath, 0o600); // restore so tmpdir cleanup works
  }

  assert.deepEqual(snapshot.brandVoice, []);
  assert.deepEqual(snapshot.forbiddenPhrases, []);
  assert.equal(snapshot.corrupted.length, 0);
  assert.match(store.getSessionOnlyWarnings().join("\n"), /설정 저장 공간을 읽을 수 없습니다/);
});
