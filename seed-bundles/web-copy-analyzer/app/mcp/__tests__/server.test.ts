import { test } from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { createServer } from "../server.js";

async function tmpRoot(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), "wca-mcp-"));
}

const THIS_DIR = path.dirname(fileURLToPath(import.meta.url));
const AGENTS_MD_PATH = path.resolve(THIS_DIR, "../../../worker/agent.md");

async function connectedClient(rootDir: string) {
  const created = await createServer({ rootDir, agentsMdPath: AGENTS_MD_PATH, customToolsDir: path.join(rootDir, "custom-tools"), log: () => {} });
  const [serverTransport, clientTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: "test-client", version: "0.0.0" });
  await Promise.all([created.server.connect(serverTransport), client.connect(clientTransport)]);
  return { client, created };
}

test("server registers the 12 core tools + 3 knowledge tools (+ any custom-tools) and instructions is non-empty", async () => {
  const rootDir = await tmpRoot();
  const { client, created } = await connectedClient(rootDir);

  const instructions = client.getInstructions();
  assert.ok(instructions && instructions.length > 0);
  assert.match(instructions, /전환 카피 컨설턴트/); // AGENTS.md §①

  const { tools } = await client.listTools();
  const names = tools.map((t) => t.name).sort();
  assert.equal(names.length, 15);
  assert.deepEqual(
    names,
    [
      "compare_report",
      "delete_persona",
      "diagnose_section",
      "fetch_page",
      "get_persona",
      "knowledge_neighbors",
      "learn_knowledge",
      "list_personas",
      "parse_sections",
      "readability_scorecard",
      "remember",
      "rewrite_section",
      "save_persona",
      "save_workflow",
      "search_knowledge",
    ]
  );
  assert.equal(created.loadedCustomToolNames.length, 0);
});

test("persona://merged resource is registered and readable, reflects growth-layer state", async () => {
  const rootDir = await tmpRoot();
  const { client } = await connectedClient(rootDir);

  const { resources } = await client.listResources();
  assert.equal(resources.length, 1);
  assert.equal(resources[0]?.uri, "persona://merged");

  const before = await client.readResource({ uri: "persona://merged" });
  const beforeText = String((before.contents[0] as { text?: string })?.text ?? "");
  assert.doesNotMatch(beforeText, /always use formal/);

  await client.callTool({
    name: "remember",
    arguments: { kind: "brand_voice", content: "always use formal 존댓말" },
  });

  const after = await client.readResource({ uri: "persona://merged" });
  const afterText = String((after.contents[0] as { text?: string })?.text ?? "");
  assert.match(afterText, /always use formal/);
});

test("tools/call: save_persona -> list_personas -> get_persona round-trip through the real wire boundary", async () => {
  const rootDir = await tmpRoot();
  const { client } = await connectedClient(rootDir);

  const saveResult = await client.callTool({
    name: "save_persona",
    arguments: {
      name: "Solo Founder Sam",
      attributes: { role: "1인 창업자", pains: ["no time"], vocabulary: ["MRR"], buying_triggers: ["fast setup"] },
    },
  });
  assert.equal(saveResult.isError, undefined);
  const saved = JSON.parse((saveResult.content as Array<{ text: string }>)[0]?.text ?? "{}");
  assert.equal(saved.id, "solo-founder-sam");

  const getResult = await client.callTool({ name: "get_persona", arguments: { id: "solo-founder-sam" } });
  const persona = JSON.parse((getResult.content as Array<{ text: string }>)[0]?.text ?? "{}");
  assert.equal(persona.name, "Solo Founder Sam");
  assert.deepEqual(persona.buying_triggers, ["fast setup"]); // snake_case on the wire
});

test("tools/call: parse_sections -> readability_scorecard chain works over the wire (snake_case in/out)", async () => {
  const rootDir = await tmpRoot();
  const { client } = await connectedClient(rootDir);

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

test("tools/call: get_persona for a missing id returns an MCP tool error carrying 문제표 #8's message", async () => {
  const rootDir = await tmpRoot();
  const { client } = await connectedClient(rootDir);
  const result = await client.callTool({ name: "get_persona", arguments: { id: "ghost" } });
  assert.equal(result.isError, true);
  const text = (result.content as Array<{ text: string }>)[0]?.text ?? "";
  assert.match(text, /ghost.*페르소나가 없습니다/);
});

test("tools/call: input exceeding a schema cap is rejected before reaching core (§5)", async () => {
  const rootDir = await tmpRoot();
  const { client } = await connectedClient(rootDir);
  const result = await client.callTool({
    name: "remember",
    arguments: { kind: "decision", content: "x".repeat(2001) },
  });
  assert.equal(result.isError, true);
});

test("custom-tools are loaded and callable alongside the 12 core tools", async () => {
  const rootDir = await tmpRoot();
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

  const created = await createServer({ rootDir, agentsMdPath: AGENTS_MD_PATH, customToolsDir: customDir, log: () => {} });
  const [serverTransport, clientTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: "test-client", version: "0.0.0" });
  await Promise.all([created.server.connect(serverTransport), client.connect(clientTransport)]);

  assert.deepEqual(created.loadedCustomToolNames, ["custom_echo"]);
  const { tools } = await client.listTools();
  assert.ok(tools.some((t) => t.name === "custom_echo"));

  const result = await client.callTool({ name: "custom_echo", arguments: { text: "hi" } });
  const parsed = JSON.parse((result.content as Array<{ text: string }>)[0]?.text ?? "{}");
  assert.equal(parsed.echoed, "hi");
});

test("문제표 #20: createServer boots session-only (with a degraded warning) instead of crashing when voice.md is unreadable at startup", async () => {
  const rootDir = await tmpRoot();
  const voicePath = path.join(rootDir, "voice.md");
  await fs.mkdir(rootDir, { recursive: true });
  await fs.writeFile(voicePath, "schema_version:1\n", "utf-8");
  await fs.chmod(voicePath, 0o000);

  const logs: string[] = [];
  let created;
  try {
    created = await createServer({
      rootDir,
      agentsMdPath: AGENTS_MD_PATH,
      customToolsDir: path.join(rootDir, "custom-tools"),
      log: (msg) => logs.push(msg),
    });
  } finally {
    await fs.chmod(voicePath, 0o600); // restore so tmpdir cleanup works
  }

  assert.ok(created, "createServer must not throw on a read-side storage-unavailable error");
  assert.ok(logs.some((l) => /설정 저장 공간을 읽을 수 없습니다/.test(l)), "expected the degraded-mode warning on the log/stderr channel");

  // Still a usable, connectable session (session-only / degraded mode, not a crash).
  const [serverTransport, clientTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: "test-client", version: "0.0.0" });
  await Promise.all([created.server.connect(serverTransport), client.connect(clientTransport)]);
  const { tools } = await client.listTools();
  assert.ok(tools.length > 0);
});
