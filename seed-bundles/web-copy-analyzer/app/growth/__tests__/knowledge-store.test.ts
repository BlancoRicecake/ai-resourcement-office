import { test } from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { KnowledgeStore } from "../knowledge-store.js";
import { parseKnowledgeNode } from "../../core/knowledge.js";
import { knowledgeDir } from "../paths.js";

async function tmp(prefix: string): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), prefix));
}

/**
 * A store wired entirely to tmp dirs (never the real ~/.web-copy-analyzer/ home
 * or the real seed dir). seedGraphPath points at a non-existent file so the
 * store falls back to parsing our tmp seed .md dir.
 */
async function makeStore(now?: () => string): Promise<{ store: KnowledgeStore; rootDir: string; seedDir: string }> {
  const rootDir = await tmp("wca-know-root-");
  const seedDir = await tmp("wca-know-seed-");
  await fs.writeFile(
    path.join(seedDir, "headline-clarity.md"),
    ["---", "id: headline-clarity", "title: 헤드라인 명확성", "tags:", "  - clarity", "source: seed", "confidence: high", "---", "명확성 우선 [[f-pattern]]"].join("\n"),
    "utf-8"
  );
  await fs.writeFile(
    path.join(seedDir, "f-pattern.md"),
    ["---", "id: f-pattern", "title: F-패턴", "tags:", "  - layout", "source: seed", "confidence: high", "---", "스캔 동선 [[headline-clarity]]"].join("\n"),
    "utf-8"
  );
  const store = new KnowledgeStore({
    rootDir,
    seedDir,
    seedGraphPath: path.join(seedDir, "no-graph.json"),
    ...(now ? { now } : {}),
  });
  return { store, rootDir, seedDir };
}

test("searchKnowledge over seed-only graph (no learned yet)", async () => {
  const { store } = await makeStore();
  const res = await store.searchKnowledge("clarity", 10);
  assert.equal(res[0]?.id, "headline-clarity");
  assert.equal(res[0]?.source, "seed");
});

test("knowledgeNeighbors traverses seed edges (bidirectional)", async () => {
  const { store } = await makeStore();
  const res = await store.knowledgeNeighbors("headline-clarity", 1);
  assert.deepEqual(res.neighbors.map((n) => n.id), ["f-pattern"]);
});

test("learn_knowledge success: writes a well-formed learned node into the growth root; becomes searchable in the merged graph", async () => {
  const { store, rootDir } = await makeStore(() => "2026-07-09T08:30:00.000Z");
  const result = await store.learnKnowledge({
    title: "SaaS 랜딩 반복 패턴",
    body: "무료 체험 CTA가 히어로에 반복 등장한다.",
    tags: ["saas", "pattern"],
    links: ["headline-clarity"],
    evidence: ["https://example.com/observed"],
  });
  assert.equal(result.learned, true);
  assert.equal(result.rejected, undefined);
  assert.ok(result.id?.startsWith("saas-랜딩-반복-패턴-"));
  assert.match(result.shown, /학습함: SaaS 랜딩 반복 패턴/);

  // File written under the growth root's knowledge/ dir (never real home).
  assert.ok(result.path?.startsWith(rootDir));
  const raw = await fs.readFile(result.path!, "utf-8");
  const node = parseKnowledgeNode(raw);
  assert.equal(node.source, "learned");
  assert.equal(node.confidence, "low");
  assert.equal(node.created, "2026-07-09");
  assert.deepEqual(node.tags, ["saas", "pattern"]);
  assert.deepEqual(node.evidence, ["https://example.com/observed"]);
  assert.match(node.body, /\[\[headline-clarity\]\]/); // links became wikilinks

  // Cross-restart continuity: a NEW store over the same growth root sees it (survives restart).
  const restarted = new KnowledgeStore({ rootDir, seedDir: (await makeStore()).seedDir, seedGraphPath: path.join(rootDir, "no.json") });
  const merged = await restarted.searchKnowledge("SaaS 랜딩", 10);
  assert.ok(merged.some((r) => r.id === result.id && r.source === "learned"));
});

test("learn_knowledge hygiene REJECTION: a fake email (PII) is rejected, nothing written", async () => {
  const { store, rootDir } = await makeStore();
  const result = await store.learnKnowledge({
    title: "고객 연락처 패턴",
    body: "담당자 이메일은 jane@example.com 이다.",
  });
  assert.equal(result.learned, false);
  assert.equal(result.rejected, true);
  assert.equal(result.shown, "이 정보(개인정보/미공개 매출)는 기억하지 않습니다.");
  // No learned dir/file created.
  await assert.rejects(() => fs.readdir(knowledgeDir(rootDir)));
});

test("learn_knowledge hygiene REJECTION: undisclosed revenue (매출 5000만원) is rejected", async () => {
  const { store } = await makeStore();
  const result = await store.learnKnowledge({
    title: "이 업종 성과",
    body: "이 고객사는 매출 5000만원을 기록했다.",
  });
  assert.equal(result.learned, false);
  assert.equal(result.rejected, true);
  assert.equal(result.shown, "이 정보(개인정보/미공개 매출)는 기억하지 않습니다.");
});

test("learn_knowledge: empty title/body rejected before any write", async () => {
  const { store } = await makeStore();
  await assert.rejects(() => store.learnKnowledge({ title: "  ", body: "x" }));
  await assert.rejects(() => store.learnKnowledge({ title: "x", body: "  " }));
});
