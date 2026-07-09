#!/usr/bin/env node
/**
 * Builds the prebuilt SEED knowledge graph snapshot
 * (worker/knowledge/graph.json) from the seed nodes at worker/knowledge/*.md.
 * This is the verified, seed-only, reproducible artifact the runtime query
 * adapter loads and merges with LIVE learned nodes (growth root). Run via tsx
 * so it can import the pure core graph builder directly (no logic duplication):
 *   node --import tsx scripts/gen-graph.mjs
 *
 * VERIFY GATE (fails the build): every [[wikilink]] in a seed node must resolve
 * to an existing seed node id; no self-loops; no duplicate ids. The committed
 * graph.json must round-trip (rebuild == committed) — enforced by the
 * knowledge-seed test.
 */
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import {
  parseKnowledgeNode,
  buildGraph,
  serializeGraphJson,
  findDanglingEdges,
  findSelfLoops,
} from "../core/knowledge.ts";

const APP_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url))); // app/
const ROOT = path.dirname(APP_DIR); // bundle root
const SEED_DIR = path.join(ROOT, "worker", "knowledge");
const OUT_PATH = path.join(SEED_DIR, "graph.json");

function main() {
  const files = readdirSync(SEED_DIR)
    .filter((f) => f.endsWith(".md"))
    .sort();

  const nodes = [];
  const seenIds = new Set();
  for (const file of files) {
    const raw = readFileSync(path.join(SEED_DIR, file), "utf8");
    const node = parseKnowledgeNode(raw, { fallbackSource: "seed", fallbackConfidence: "high" });
    const expectedId = file.slice(0, -".md".length);
    if (node.id !== expectedId) {
      throw new Error(`gen-graph: '${file}' 의 frontmatter id('${node.id}')가 파일명과 다릅니다.`);
    }
    if (seenIds.has(node.id)) {
      throw new Error(`gen-graph: 중복 seed 노드 id '${node.id}'.`);
    }
    seenIds.add(node.id);
    nodes.push(node);
  }

  const graph = buildGraph(nodes);

  const dangling = findDanglingEdges(graph);
  if (dangling.length > 0) {
    const list = dangling.map((e) => `${e.from} -> [[${e.to}]]`).join(", ");
    throw new Error(`gen-graph: 끊어진 seed 인용(dangling wikilink)이 있습니다: ${list}`);
  }
  const selfLoops = findSelfLoops(graph);
  if (selfLoops.length > 0) {
    const list = selfLoops.map((e) => e.from).join(", ");
    throw new Error(`gen-graph: seed 노드에 self-loop가 있습니다: ${list}`);
  }

  const json = serializeGraphJson(nodes);
  writeFileSync(OUT_PATH, json, "utf8");
  console.log(`generated ${path.relative(ROOT, OUT_PATH)} (nodes: ${nodes.length}, edges: ${graph.edges.length})`);
}

main();
