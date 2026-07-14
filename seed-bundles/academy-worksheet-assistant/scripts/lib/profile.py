# -*- coding: utf-8 -*-
"""사용자 설정과 사용자 제공 교육과정 지식팩을 읽고 검증한다."""
from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "config" / "profile.json"
CATALOG_PATH = ROOT / "knowledge" / "curriculum.json"


def _load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_profile(path=None):
    target = Path(path) if path else PROFILE_PATH
    if not target.is_file():
        raise ValueError("초기 설정이 없습니다. 에이전트에게 '초기 설정을 시작해줘'라고 요청하세요. 명령어 방식은 `python setup.py`입니다.")
    return _load(target)


def load_catalog(path=None):
    target = Path(path) if path else CATALOG_PATH
    if not target.is_file():
        raise ValueError("교육과정 지식팩이 없습니다: knowledge/curriculum.json")
    return _load(target)


def validate_profile(profile):
    errors = []
    for key in ("subject", "school_level", "grade", "exam_year", "curriculum"):
        if not profile.get(key):
            errors.append(f"profile.{key} 누락")
    formats = profile.get("output_formats")
    if not isinstance(formats, list) or not formats:
        errors.append("profile.output_formats는 1개 이상의 배열이어야 함")
    unsupported = sorted(set(formats or []) - {"hwp", "pdf"})
    if unsupported:
        errors.append(f"지원하지 않는 출력 형식: {', '.join(unsupported)}")
    if profile.get("input_format") != "pdf":
        errors.append("현재 지원하는 입력 형식은 pdf뿐임")
    return errors


def standard_index(catalog=None):
    catalog = catalog or load_catalog()
    result = {}
    for unit in catalog.get("units") or []:
        for standard in unit.get("standards") or []:
            code = str(standard.get("code") or "").strip()
            if code:
                result[code] = {
                    **standard,
                    "unit_code": str(unit.get("code") or ""),
                    "unit_title": unit.get("title"),
                }
    return result


def validate_catalog(catalog, profile=None):
    errors = []
    profile = profile or load_profile()
    if catalog.get("subject") != profile.get("subject"):
        errors.append("지식팩 과목과 사용자 설정 과목이 다름")
    if catalog.get("curriculum") != profile.get("curriculum"):
        errors.append("지식팩 교육과정과 사용자 설정 교육과정이 다름")
    if catalog.get("approval", {}).get("status") != "approved":
        errors.append("교육과정 지식팩이 사용자 승인 상태가 아님")
    sources = catalog.get("sources") or []
    if not any(item.get("title") and item.get("reference") for item in sources if isinstance(item, dict)):
        errors.append("확인 가능한 교육과정 출처가 없음")
    units = catalog.get("units") or []
    if not units:
        errors.append("교육과정 단원이 비어 있음")
    seen = set()
    for unit in units:
        code = str(unit.get("code") or "").strip()
        if not code or not unit.get("title"):
            errors.append("단원 code/title 누락")
        standards = unit.get("standards") or []
        if not standards:
            errors.append(f"단원 {code or '?'}: 성취기준이 비어 있음")
        for standard in standards:
            standard_code = str(standard.get("code") or "").strip()
            if not standard_code or not standard.get("statement"):
                errors.append(f"단원 {code or '?'}: 성취기준 code/statement 누락")
            elif standard_code in seen:
                errors.append(f"성취기준 코드 중복: {standard_code}")
            seen.add(standard_code)
    return errors


def readiness_errors(profile=None, catalog=None):
    profile = profile or load_profile()
    errors = validate_profile(profile)
    if profile.get("knowledge_status") != "ready":
        errors.append("profile.knowledge_status가 ready가 아님")
    try:
        catalog = catalog or load_catalog()
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    errors.extend(validate_catalog(catalog, profile))
    return errors


def empty_alignment():
    return {
        "status": "unreviewed",
        "unit_code": None,
        "standard_code": None,
        "confidence": None,
        "evidence": [],
        "alternatives": [],
        "review_required": True,
        "review_reason": "사용자 승인 교육과정 기준으로 미분류",
    }


def validate_alignment(alignment, catalog=None):
    if not isinstance(alignment, dict):
        return ["alignment가 객체가 아님"]
    if alignment.get("status") in (None, "unreviewed"):
        return []
    errors = []
    try:
        index = standard_index(catalog)
    except ValueError as exc:
        return [str(exc)]
    standard_code = alignment.get("standard_code")
    entry = index.get(standard_code)
    if not entry:
        errors.append(f"지식팩에 없는 성취기준: {standard_code}")
        return errors
    if str(alignment.get("unit_code")) != str(entry["unit_code"]):
        errors.append("성취기준과 단원 코드가 일치하지 않음")
    confidence = alignment.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append("confidence는 0~1 숫자여야 함")
    if not any(str(item).strip() for item in alignment.get("evidence") or []):
        errors.append("확정 태깅에는 evidence가 1개 이상 필요")
    if isinstance(confidence, (int, float)) and confidence < 0.8 and not alignment.get("review_required"):
        errors.append("confidence 0.8 미만은 review_required=true여야 함")
    return errors


def sync_knowledge_status(profile, catalog_path=None):
    """승인된 지식팩의 실제 상태를 설정 파일에 반영한다."""
    catalog_path = Path(catalog_path) if catalog_path else CATALOG_PATH
    try:
        catalog = load_catalog(catalog_path)
        ready = not validate_catalog(catalog, profile)
    except ValueError:
        ready = False
    profile["knowledge_status"] = "ready" if ready else "pending"
    return profile
