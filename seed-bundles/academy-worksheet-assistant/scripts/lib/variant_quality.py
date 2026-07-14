# -*- coding: utf-8 -*-
"""과목 불문 변형문제 설계서와 출고 전 품질 게이트."""
from __future__ import annotations

import re

from .profile import readiness_errors, standard_index


CHOICE_SYMBOLS = "①②③④⑤⑥⑦⑧⑨⑩"


def _blocks(item):
    return item.get("blocks") or []


def choice_count(item):
    count = 0
    for block in _blocks(item):
        if block.get("t") == "choices":
            count += len(block.get("items") or [])
        elif block.get("t") == "choice_table":
            count += len(block.get("rows") or [])
    return count


def choice_texts(item):
    result = []
    for block in _blocks(item):
        if block.get("t") == "choices":
            result.extend(str(value).strip() for value in block.get("items") or [])
        elif block.get("t") == "choice_table":
            result.extend(" | ".join(map(str, row)).strip() for row in block.get("rows") or [])
    return result


def image_files(item):
    return [block.get("file") for block in _blocks(item) if block.get("t") == "image" and block.get("file")]


def _normal_choice(text):
    return re.sub(rf"^[{CHOICE_SYMBOLS}]\s*", "", str(text)).strip()


def _issue(severity, code, message):
    return {"severity": severity, "code": code, "message": message}


def validate_variant(exam, question, variant, output_gate=False):
    issues = []
    meta = exam.get("meta", {})
    prefix = f"문항 {question.get('no')} 변형 {variant.get('id') or '?'}"
    spec = variant.get("variant_spec")

    if output_gate:
        for error in readiness_errors():
            issues.append(_issue("error", "knowledge.not_ready", f"{prefix}: {error}"))

    for key in ("id", "blocks", "answer", "change_note", "explanation"):
        if not variant.get(key):
            issues.append(_issue("error", f"variant.{key}.missing", f"{prefix}: {key} 누락"))

    original_count = choice_count(question)
    variant_count = choice_count(variant)
    if original_count and variant_count != original_count:
        issues.append(_issue("error", "choices.count", f"{prefix}: 선지 수가 원문과 다름"))
    if variant_count:
        if variant.get("answer") not in set(CHOICE_SYMBOLS[:variant_count]):
            issues.append(_issue("error", "answer.range", f"{prefix}: 정답이 선지 범위를 벗어남"))
        normalized = [_normal_choice(value) for value in choice_texts(variant)]
        meaningful = [value for value in normalized if value]
        if len(meaningful) != len(set(meaningful)):
            issues.append(_issue("error", "choices.duplicate", f"{prefix}: 선지 문자열 중복"))

    alignment = question.get("alignment") or {}
    if alignment.get("status") != "confirmed" or alignment.get("review_required"):
        issues.append(_issue("error", "alignment.unconfirmed", f"{prefix}: 성취기준 확정 전에는 변형할 수 없음"))

    if not isinstance(spec, dict):
        issues.append(_issue("error", "variant_spec.missing", f"{prefix}: VariantSpec 누락"))
        return issues

    required = (
        "schema_version", "curriculum", "unit_code", "standard_code", "intent_invariants",
        "mutable_elements", "difficulty", "answer_proof", "independent_solution", "applied_checks",
    )
    for key in required:
        if spec.get(key) in (None, "", []):
            issues.append(_issue("error", f"variant_spec.{key}.missing", f"{prefix}: VariantSpec.{key} 누락"))
    if not isinstance(spec.get("asset_contracts"), list):
        issues.append(_issue("error", "variant_spec.asset_contracts.missing", f"{prefix}: asset_contracts 배열 누락"))

    if spec.get("curriculum") != meta.get("curriculum"):
        issues.append(_issue("error", "curriculum.mismatch", f"{prefix}: 교육과정 불일치"))
    if spec.get("standard_code") != alignment.get("standard_code"):
        issues.append(_issue("error", "standard.mismatch", f"{prefix}: 성취기준 코드 불일치"))
    if str(spec.get("unit_code")) != str(alignment.get("unit_code")):
        issues.append(_issue("error", "unit.mismatch", f"{prefix}: 단원 코드 불일치"))

    intent = str(question.get("intent") or "").strip()
    invariants = [str(value).strip() for value in spec.get("intent_invariants") or []]
    if intent and intent not in invariants:
        issues.append(_issue("error", "intent.not_preserved", f"{prefix}: 출제 의도가 불변조건에 없음"))

    difficulty = spec.get("difficulty") or {}
    original_steps = difficulty.get("original_reasoning_steps")
    variant_steps = difficulty.get("variant_reasoning_steps")
    if not isinstance(original_steps, int) or original_steps < 1:
        issues.append(_issue("error", "difficulty.original", f"{prefix}: 원문 추론 단계 오류"))
    if not isinstance(variant_steps, int) or variant_steps < 1:
        issues.append(_issue("error", "difficulty.variant", f"{prefix}: 변형 추론 단계 오류"))
    if isinstance(original_steps, int) and isinstance(variant_steps, int) and abs(original_steps - variant_steps) > 1:
        issues.append(_issue("error", "difficulty.drift", f"{prefix}: 난이도 추론 단계 차이가 1을 초과함"))

    solution = spec.get("independent_solution") or {}
    if solution.get("status") != "passed" or solution.get("blinded") is not True:
        issues.append(_issue("error", "solution.not_passed", f"{prefix}: 블라인드 독립 풀이가 통과하지 않음"))
    if solution.get("answer") != variant.get("answer"):
        issues.append(_issue("error", "solution.answer_mismatch", f"{prefix}: 독립 풀이 정답 불일치"))
    if not solution.get("evidence"):
        issues.append(_issue("error", "solution.evidence_missing", f"{prefix}: 독립 풀이 근거 누락"))

    reused = set(image_files(question)) & set(image_files(variant))
    contracts = {item.get("file"): item for item in spec.get("asset_contracts") or [] if isinstance(item, dict)}
    for filename in reused:
        contract = contracts.get(filename)
        if not contract:
            issues.append(_issue("error", "asset.contract_missing", f"{prefix}: 재사용 그림 계약 누락"))
        elif contract.get("verification_status") not in ("verified", "human_reviewed") or contract.get("conflicts"):
            issues.append(_issue("error", "asset.not_verified", f"{prefix}: 재사용 그림 검증 미완료 또는 충돌"))

    try:
        if spec.get("standard_code") not in standard_index():
            issues.append(_issue("error", "standard.unknown", f"{prefix}: 승인 지식팩에 없는 성취기준"))
    except ValueError as exc:
        issues.append(_issue("error", "knowledge.lookup", f"{prefix}: 지식 조회 실패: {exc}"))

    qa = variant.get("qa") or {}
    if output_gate and qa.get("status") != "pass":
        issues.append(_issue("error", "qa.not_passed", f"{prefix}: 독립 검수 상태가 pass가 아님"))
    elif qa.get("status") not in ("pass", "flag", "fail"):
        issues.append(_issue("warning", "qa.unreviewed", f"{prefix}: 독립 검수 미완료"))
    return issues


def validate_exam_variants(exam, output_gate=False):
    issues = []
    count = 0
    for question in exam.get("questions") or []:
        for variant in question.get("variants") or []:
            count += 1
            issues.extend(validate_variant(exam, question, variant, output_gate=output_gate))
    if output_gate and count == 0:
        issues.append(_issue("error", "variants.empty", "변형문제지에 출력할 변형문항이 없음"))
    return issues


def blocking_messages(issues):
    return [item["message"] for item in issues if item.get("severity") == "error"]
