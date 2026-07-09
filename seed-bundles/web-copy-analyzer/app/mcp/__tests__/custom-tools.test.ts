import { test } from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { loadCustomTools } from "../custom-tools.js";

async function tmpDir(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), "wca-custom-tools-"));
}

test("loadCustomTools: missing directory returns empty (no failures) — server still boots", async () => {
  const result = await loadCustomTools(path.join(os.tmpdir(), "does-not-exist-" + Date.now()));
  assert.deepEqual(result, { loaded: [], failures: [] });
});

test("loadCustomTools: registers a well-formed custom tool script", async () => {
  const dir = await tmpDir();
  await fs.writeFile(
    path.join(dir, "ping.mjs"),
    `export default {
      definition: { name: "custom_ping", inputSchema: { type: "object", properties: {}, additionalProperties: false } },
      async execute() { return { pong: true }; },
    };`,
    "utf-8"
  );

  const result = await loadCustomTools(dir);
  assert.equal(result.failures.length, 0);
  assert.equal(result.loaded.length, 1);
  assert.equal(result.loaded[0]?.definition.name, "custom_ping");
  assert.deepEqual(await result.loaded[0]?.execute({}, {} as never), { pong: true });
});

test("문제표 #15: a broken custom-tool script is skipped with a load-failure message, doesn't crash the loader", async () => {
  const dir = await tmpDir();
  await fs.writeFile(path.join(dir, "broken.mjs"), `throw new Error("boom during module init");`, "utf-8");
  await fs.writeFile(
    path.join(dir, "good.mjs"),
    `export default {
      definition: { name: "custom_good", inputSchema: { type: "object", properties: {}, additionalProperties: false } },
      async execute() { return { ok: true }; },
    };`,
    "utf-8"
  );

  const result = await loadCustomTools(dir);
  assert.equal(result.loaded.length, 1);
  assert.equal(result.loaded[0]?.definition.name, "custom_good");
  assert.equal(result.failures.length, 1);
  assert.match(result.failures[0] ?? "", /broken\.mjs.*로드 실패/);
});

test("loadCustomTools: rejects a script missing the {definition, execute} shape", async () => {
  const dir = await tmpDir();
  await fs.writeFile(path.join(dir, "shapeless.mjs"), `export default { notATool: true };`, "utf-8");
  const result = await loadCustomTools(dir);
  assert.equal(result.loaded.length, 0);
  assert.equal(result.failures.length, 1);
});
