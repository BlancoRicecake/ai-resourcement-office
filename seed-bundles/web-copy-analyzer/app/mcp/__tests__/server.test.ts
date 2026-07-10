import { test } from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { createServer } from "../server.js";

async function tmpDir(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), "wca-mcp-"));
}

const THIS_DIR = path.dirname(fileURLToPath(import.meta.url));
const AGENTS_MD_PATH = path.resolve(THIS_DIR, "../../../worker/agent.md");

async function connectedClient(customToolsDir: string) {
  const created = await createServer({ agentsMdPath: AGENTS_MD_PATH, customToolsDir, log: () => {} });
  const [serverTransport, clientTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: "test-client", version: "0.0.0" });
  await Promise.all([created.server.connect(serverTransport), client.connect(clientTransport)]);
  return { client, created };
}

test("server registers the 6 deterministic tools (+ any custom-tools) and instructions is non-empty", async () => {
  const { client, created } = await connectedClient(path.join(await tmpDir(), "custom-tools"));

  const instructions = client.getInstructions();
  assert.ok(instructions && instructions.length > 0);
  assert.match(instructions, /전환 카피 컨설턴트/); // worker/agent.md §①

  const { tools } = await client.listTools();
  const names = tools.map((t) => t.name).sort();
  assert.equal(names.length, 6);
  assert.deepEqual(names, [
    "compare_report",
    "diagnose_section",
    "fetch_page",
    "parse_sections",
    "readability_scorecard",
    "rewrite_section",
  ]);
  assert.equal(created.loadedCustomToolNames.length, 0);
});

test("server does NOT register any resources (no growth-layer persona://merged)", async () => {
  const { client } = await connectedClient(path.join(await tmpDir(), "custom-tools"));
  await assert.rejects(() => client.listResources());
});

test("tools/call: parse_sections -> readability_scorecard chain works over the wire (snake_case in/out)", async () => {
  const { client } = await connectedClient(path.join(await tmpDir(), "custom-tools"));

  const html = `<html><body>
    <section><h1>Ship your side project faster</h1><p>Built for indie hackers.</p><a>Get Started</a></section>
  </body></html>`;
  const parseResult = await client.callTool({ name: "parse_sections", arguments: { html } });
  const parsedPage = JSON.parse((parseResult.content as Array<{ text: string }>)[0]?.text ?? "{}");
  assert.ok(Array.isArray(parsedPage.sections));
  assert.ok("parse_quality" in parsedPage);

  const scoreResult = await client.callTool({ name: "readability_scorecard", arguments: { parsed_page: parsedPage } });
  const scorecard = JSON.parse((scoreResult.content as Array<{ text: string }>)[0]?.text ?? "{}");
  assert.ok("cta_inventory" in scorecard);
  assert.ok("we_you_ratio" in scorecard);
});

test("tools/call: diagnose_section takes an inline persona object (no persona store) and returns a diagnosis payload", async () => {
  const { client } = await connectedClient(path.join(await tmpDir(), "custom-tools"));

  const html = `<html><body>
    <section><h1>Ship your side project faster</h1><p>Built for indie hackers.</p><a>Get Started</a></section>
  </body></html>`;
  const parseResult = await client.callTool({ name: "parse_sections", arguments: { html } });
  const parsedPage = JSON.parse((parseResult.content as Array<{ text: string }>)[0]?.text ?? "{}");

  const persona = {
    name: "부트스트랩 창업자",
    attributes: { role: "1인 창업자", pains: ["예산이 빠듯하다"], vocabulary: ["5분 안에", "무료 체험"] },
  };
  const diag = await client.callTool({
    name: "diagnose_section",
    arguments: { parsed_page: parsedPage, persona, scope: "above_fold" },
  });
  assert.equal(diag.isError, undefined);
  const brief = JSON.parse((diag.content as Array<{ text: string }>)[0]?.text ?? "{}");
  assert.equal(brief.brief_kind, "diagnosis");
  assert.equal(brief.persona.name, "부트스트랩 창업자"); // normalized persona echoed back on the wire
  assert.ok(Array.isArray(brief.attribution_frame));
});

test("tools/call: input exceeding a schema cap is rejected before reaching core (§5)", async () => {
  const { client } = await connectedClient(path.join(await tmpDir(), "custom-tools"));
  const result = await client.callTool({
    name: "compare_report",
    arguments: { before: {}, after: [{ section_id: "s1", rewritten_text: "x".repeat(20001) }] },
  });
  assert.equal(result.isError, true);
});

test("custom-tools are loaded and callable alongside the deterministic core tools", async () => {
  const rootDir = await tmpDir();
  const customDir = path.join(rootDir, "custom-tools");
  await fs.mkdir(customDir, { recursive: true });
  await fs.writeFile(
    path.join(customDir, "echo.mjs"),
    `export default {
      definition: { name: "custom_echo", inputSchema: { type: "object", properties: { text: { type: "string" } }, additionalProperties: false } },
      async execute(args) { return { echoed: args.text }; },
    };`,
    "utf-8"
  );

  const { client, created } = await connectedClient(customDir);
  assert.deepEqual(created.loadedCustomToolNames, ["custom_echo"]);
  const { tools } = await client.listTools();
  assert.ok(tools.some((t) => t.name === "custom_echo"));

  const result = await client.callTool({ name: "custom_echo", arguments: { text: "hi" } });
  const parsed = JSON.parse((result.content as Array<{ text: string }>)[0]?.text ?? "{}");
  assert.equal(parsed.echoed, "hi");
});
