/**
 * mergeInstructions — merges the deployment persona (AGENTS.md, static /
 * update-replaceable) with the user's growth layer (~/.web-copy-analyzer/,
 * update-immutable), user-first on conflict (design.md §6-2). Pure/sync so
 * it's trivially testable without I/O — callers gather the GrowthSnapshot
 * via GrowthStore.buildGrowthSnapshot() first.
 */

import type { GrowthSnapshot } from "./types.js";

function renderGrowthSection(growth: GrowthSnapshot): string | undefined {
  const parts: string[] = [];

  if (growth.brandVoice.length > 0 || growth.forbiddenPhrases.length > 0) {
    parts.push("### 브랜드 보이스 / 금지 표현 (사용자 설정 — 아래 ①~④보다 우선)");
    for (const v of growth.brandVoice) parts.push(`- 보이스: ${v}`);
    for (const f of growth.forbiddenPhrases) parts.push(`- 금지 표현(사용 금지): ${f}`);
  }

  if (growth.personas.length > 0) {
    parts.push("### 저장된 타깃 페르소나 (list_personas/get_persona로 조회)");
    for (const p of growth.personas) parts.push(`- ${p.name} (id: ${p.id}, ${p.role})`);
  }

  if (growth.corrupted.length > 0) {
    parts.push(`### 참고: 성장 기록 ${growth.corrupted.length}건은 손상되어 건너뛰었습니다.`);
  }

  if (parts.length === 0) return undefined;
  return ["## 성장 레이어 (사용자 우선 설정)", ...parts].join("\n");
}

/**
 * §6-2: "충돌 시 사용자 값 우선" — the growth section is placed BEFORE the
 * static AGENTS.md text and explicitly labeled as overriding it, so a host
 * LLM reading top-to-bottom encounters the user's standing preferences
 * first and AGENTS.md's defaults second.
 */
export function mergeInstructions(agentsMd: string, growth: GrowthSnapshot): string {
  const growthSection = renderGrowthSection(growth);
  if (!growthSection) return agentsMd;
  return `${growthSection}\n\n---\n\n${agentsMd}`;
}
