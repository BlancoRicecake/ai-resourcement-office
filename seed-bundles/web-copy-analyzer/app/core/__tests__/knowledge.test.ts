import { test } from "node:test";
import assert from "node:assert/strict";
import {
  parseKnowledgeNode,
  serializeKnowledgeNode,
  extractWikilinks,
  buildGraph,
  searchKnowledge,
  knowledgeNeighbors,
  findDanglingEdges,
  findSelfLoops,
  serializeGraphJson,
  deserializeGraphNodes,
  KnowledgeParseError,
  KnowledgeNodeNotFoundError,
  type KnowledgeNode,
} from "../knowledge.js";
import {
  KNOWLEDGE_TOOL_DEFINITIONS,
  SEARCH_KNOWLEDGE_TOOL,
  KNOWLEDGE_NEIGHBORS_TOOL,
  LEARN_KNOWLEDGE_TOOL,
} from "../tool-schemas.js";

function node(id: string, opts: Partial<KnowledgeNode> = {}): KnowledgeNode {
  return {
    id,
    title: opts.title ?? id,
    tags: opts.tags ?? [],
    source: opts.source ?? "seed",
    confidence: opts.confidence ?? "high",
    evidence: opts.evidence ?? [],
    body: opts.body ?? "",
    ...(opts.created ? { created: opts.created } : {}),
  };
}

test("extractWikilinks: unique, first-appearance order, trims, ignores empties", () => {
  assert.deepEqual(extractWikilinks("see [[a]] and [[ b ]] then [[a]] and [[c]]"), ["a", "b", "c"]);
  assert.deepEqual(extractWikilinks("no links here"), []);
});

test("parseKnowledgeNode: reads frontmatter (block arrays + scalars) and body, defaults source/confidence", () => {
  const raw = [
    "---",
    "id: hero",
    "title: 히어로",
    "tags:",
    "  - above-fold",
    "  - clarity",
    "source: seed",
    "confidence: high",
    "---",
    "본문 [[attention-ratio]] 링크",
  ].join("\n");
  const n = parseKnowledgeNode(raw);
  assert.equal(n.id, "hero");
  assert.equal(n.title, "히어로");
  assert.deepEqual(n.tags, ["above-fold", "clarity"]);
  assert.equal(n.source, "seed");
  assert.equal(n.confidence, "high");
  assert.match(n.body, /attention-ratio/);
});

test("parseKnowledgeNode: fallbackSource/confidence applied when frontmatter omits them", () => {
  const raw = ["---", "id: x", "title: X", "---", "body"].join("\n");
  const n = parseKnowledgeNode(raw, { fallbackSource: "learned", fallbackConfidence: "low" });
  assert.equal(n.source, "learned");
  assert.equal(n.confidence, "low");
});

test("parseKnowledgeNode: throws on missing fence / missing id", () => {
  assert.throws(() => parseKnowledgeNode("no frontmatter"), KnowledgeParseError);
  assert.throws(() => parseKnowledgeNode(["---", "title: no id", "---", "b"].join("\n")), KnowledgeParseError);
});

test("serializeKnowledgeNode round-trips through parseKnowledgeNode (incl. evidence [] and created)", () => {
  const original = node("learned-1", {
    title: "학습 노드",
    tags: ["voc", "trust"],
    source: "learned",
    confidence: "low",
    created: "2026-07-09",
    evidence: ["https://example.com/case", "관찰: 반복 패턴"],
    body: "본문\n\n관련: [[voc-preservation]]",
  });
  const reparsed = parseKnowledgeNode(serializeKnowledgeNode(original));
  assert.deepEqual(reparsed, original);
});

test("buildGraph: builds node map + deduped directed edges from wikilinks; first-inserted id wins on collision", () => {
  const g = buildGraph([
    node("a", { body: "[[b]] [[b]] [[c]]" }),
    node("b", { body: "[[a]]" }),
    node("c", { body: "" }),
    node("a", { title: "dup a — should not clobber", body: "[[c]]" }),
  ]);
  assert.equal(g.nodes.size, 3);
  assert.equal(g.nodes.get("a")?.title, "a"); // first wins
  // edges: a->b, a->c, b->a (a's second def ignored). deduped.
  assert.equal(g.edges.filter((e) => e.from === "a" && e.to === "b").length, 1);
  assert.ok(g.edges.some((e) => e.from === "b" && e.to === "a"));
});

test("buildGraph + findDanglingEdges/findSelfLoops: detect broken/self citations", () => {
  const g = buildGraph([node("a", { body: "[[missing]] [[a]] [[b]]" }), node("b")]);
  assert.deepEqual(findDanglingEdges(g), [{ from: "a", to: "missing" }]);
  assert.deepEqual(findSelfLoops(g), [{ from: "a", to: "a" }]);
});

test("searchKnowledge: ranks id/title/tag/body hits, deterministic, respects maxResults", () => {
  const g = buildGraph([
    node("headline-clarity", { title: "헤드라인 명확성", tags: ["clarity"], body: "명확성 우선" }),
    node("f-pattern", { title: "F-패턴", tags: ["layout"], body: "clarity 스캔에 태운다" }),
    node("attention-ratio", { title: "어텐션 비율", tags: ["cta"], body: "링크 대 목표" }),
  ]);
  const res = searchKnowledge(g, "clarity", 10);
  // headline-clarity: id includes + tag => outranks f-pattern (body only).
  assert.equal(res[0]?.id, "headline-clarity");
  assert.ok(res.some((r) => r.id === "f-pattern"));
  assert.ok(!res.some((r) => r.id === "attention-ratio")); // no "clarity" anywhere

  const limited = searchKnowledge(g, "clarity", 1);
  assert.equal(limited.length, 1);
  assert.equal(searchKnowledge(g, "   ", 10).length, 0);

  const summary = res[0];
  assert.equal(summary?.source, "seed");
  assert.equal(typeof summary?.snippet, "string");
});

test("knowledgeNeighbors: BFS depth, bidirectional reachability, caps at 3, returns traversed edges", () => {
  // chain a - b - c - d - e (via wikilinks a->b->c->d->e)
  const g = buildGraph([
    node("a", { body: "[[b]]" }),
    node("b", { body: "[[c]]" }),
    node("c", { body: "[[d]]" }),
    node("d", { body: "[[e]]" }),
    node("e"),
  ]);
  const d1 = knowledgeNeighbors(g, "a", 1);
  assert.deepEqual(d1.neighbors.map((n) => n.id), ["b"]);
  assert.equal(d1.node.id, "a");

  const d2 = knowledgeNeighbors(g, "a", 2);
  assert.deepEqual(d2.neighbors.map((n) => n.id), ["b", "c"]);
  assert.equal(d2.neighbors.find((n) => n.id === "c")?.depth, 2);

  // depth requested 9 -> clamped to 3: reaches b,c,d (not e).
  const clamped = knowledgeNeighbors(g, "a", 9);
  assert.deepEqual(clamped.neighbors.map((n) => n.id), ["b", "c", "d"]);

  // edges traversed are among the visited set only.
  assert.ok(clamped.edges.every((e) => e.to !== "e" && e.from !== "e"));
});

test("knowledgeNeighbors: unknown id throws KnowledgeNodeNotFoundError with available list", () => {
  const g = buildGraph([node("a"), node("b")]);
  assert.throws(
    () => knowledgeNeighbors(g, "nope", 1),
    (err: unknown) => {
      assert.ok(err instanceof KnowledgeNodeNotFoundError);
      assert.deepEqual(err.available, ["a", "b"]);
      return true;
    }
  );
});

test("seed + learned merge: a learned node is searchable in the same graph, provenance preserved", () => {
  const g = buildGraph([
    node("seed-x", { source: "seed", title: "시드 노드", body: "카피 원칙" }),
    node("learned-1", { source: "learned", confidence: "low", title: "학습 카피 패턴", body: "SaaS 랜딩 반복 패턴" }),
  ]);
  const res = searchKnowledge(g, "카피", 10);
  const ids = res.map((r) => r.id);
  assert.ok(ids.includes("seed-x"));
  assert.ok(ids.includes("learned-1"));
  assert.equal(res.find((r) => r.id === "learned-1")?.source, "learned");
  assert.equal(res.find((r) => r.id === "seed-x")?.source, "seed");
});

test("serializeGraphJson round-trips: rebuild from deserialized nodes == committed output", () => {
  const nodes = [
    node("b", { body: "[[a]]" }),
    node("a", { title: "A", tags: ["t"], body: "[[b]]" }),
  ];
  const json = serializeGraphJson(nodes);
  const roundTrip = serializeGraphJson(deserializeGraphNodes(json));
  assert.equal(roundTrip, json); // byte-identical
  const parsed = JSON.parse(json);
  assert.equal(parsed.version, 1);
  assert.deepEqual(parsed.nodes.map((n: KnowledgeNode) => n.id), ["a", "b"]); // sorted
});

test("knowledge tool schemas: strict (additionalProperties:false) with size caps", () => {
  assert.equal(KNOWLEDGE_TOOL_DEFINITIONS.length, 3);
  for (const tool of KNOWLEDGE_TOOL_DEFINITIONS) {
    assert.equal((tool.inputSchema as Record<string, unknown>).additionalProperties, false, `${tool.name} strict`);
  }
  assert.equal((SEARCH_KNOWLEDGE_TOOL.inputSchema as any).properties.query.maxLength, 200);
  assert.equal((KNOWLEDGE_NEIGHBORS_TOOL.inputSchema as any).properties.depth.maximum, 3);
  assert.equal((LEARN_KNOWLEDGE_TOOL.inputSchema as any).properties.body.maxLength, 20000);
});
