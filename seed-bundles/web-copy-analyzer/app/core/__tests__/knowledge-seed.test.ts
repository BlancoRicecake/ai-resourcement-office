/**
 * Verify gate for the committed SEED knowledge graph (worker/knowledge/). These
 * are HARD requirements: a dangling citation, a self-loop, a duplicate id, or a
 * stale graph.json fails the build.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import {
  parseKnowledgeNode,
  buildGraph,
  findDanglingEdges,
  findSelfLoops,
  serializeGraphJson,
  type KnowledgeNode,
} from "../knowledge.js";

const HERE = path.dirname(fileURLToPath(import.meta.url)); // app/core/__tests__
const SEED_DIR = path.join(HERE, "..", "..", "..", "worker", "knowledge");

function loadSeedNodes(): { nodes: KnowledgeNode[]; files: string[] } {
  const files = fs.readdirSync(SEED_DIR).filter((f) => f.endsWith(".md")).sort();
  const nodes = files.map((f) =>
    parseKnowledgeNode(fs.readFileSync(path.join(SEED_DIR, f), "utf-8"), {
      fallbackSource: "seed",
      fallbackConfidence: "high",
    })
  );
  return { nodes, files };
}

test("verify gate: at least 10 seed nodes, each source=seed / confidence=high, id == filename, no duplicates", () => {
  const { nodes, files } = loadSeedNodes();
  assert.ok(nodes.length >= 10, `expected >= 10 seed nodes, got ${nodes.length}`);

  const ids = new Set<string>();
  nodes.forEach((n, i) => {
    const expectedId = files[i]!.slice(0, -".md".length);
    assert.equal(n.id, expectedId, `${files[i]} frontmatter id must equal filename`);
    assert.equal(n.source, "seed", `${n.id} must be source: seed`);
    assert.equal(n.confidence, "high", `${n.id} must be confidence: high`);
    assert.ok(!ids.has(n.id), `duplicate seed id: ${n.id}`);
    ids.add(n.id);
  });
});

test("verify gate: every [[wikilink]] in every seed node resolves to an existing seed id (no dangling citations)", () => {
  const { nodes } = loadSeedNodes();
  const graph = buildGraph(nodes);
  const dangling = findDanglingEdges(graph);
  assert.deepEqual(dangling, [], `dangling seed citations: ${dangling.map((e) => `${e.from} -> [[${e.to}]]`).join(", ")}`);
});

test("verify gate: no self-loops among seed nodes", () => {
  const { nodes } = loadSeedNodes();
  const selfLoops = findSelfLoops(buildGraph(nodes));
  assert.deepEqual(selfLoops, [], `seed self-loops: ${selfLoops.map((e) => e.from).join(", ")}`);
});

test("verify gate: committed worker/knowledge/graph.json is in sync (rebuild == committed — run `npm run gen:graph`)", () => {
  const { nodes } = loadSeedNodes();
  const committed = fs.readFileSync(path.join(SEED_DIR, "graph.json"), "utf-8");
  assert.equal(serializeGraphJson(nodes), committed, "graph.json is stale — regenerate with `npm run gen:graph`");
});
