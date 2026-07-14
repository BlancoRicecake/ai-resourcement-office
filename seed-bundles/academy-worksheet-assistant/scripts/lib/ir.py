# -*- coding: utf-8 -*-
"""exam.json (중앙 IR) 로드/저장/검증/통계."""
import json
import os

REQUIRED_META = ["school", "grade", "term", "year", "subject", "curriculum", "source_pdf"]
REQUIRED_Q = ["no", "points", "type", "blocks"]


def q_choices(q):
    """문항의 선지 개수(choices/choice_table 합산)."""
    n = 0
    for b in q.get("blocks") or []:
        if b["t"] == "choices":
            n += len(b["items"])
        elif b["t"] == "choice_table":
            n += len(b["rows"])
    return n


def q_images(q):
    return [b for b in (q.get("blocks") or []) if b["t"] == "image"]


def q_text(q):
    """문항 전체를 사람이 읽는 한 덩어리 텍스트로 (검수/분석용)."""
    parts = []
    for b in q.get("blocks") or []:
        if b["t"] == "text":
            parts.append(b["text"])
        elif b["t"] == "passage":
            parts.append("<보기> " + " / ".join(b["lines"]))
        elif b["t"] == "choices":
            parts.append(" ".join(b["items"]))
        elif b["t"] == "choice_table":
            parts.append(
                " | ".join(b["headers"])
                + " ; "
                + " ; ".join("①②③④⑤"[i] + " " + ", ".join(r) for i, r in enumerate(b["rows"]))
            )
        elif b["t"] == "image":
            parts.append(f"[그림 {b['file']}]")
    return "\n".join(parts)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(exam, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(exam, f, ensure_ascii=False, indent=1)


def validate(exam):
    """스키마 필수항목 검사. 문제 목록의 문자열 리스트를 반환(비면 통과)."""
    errs = []
    meta = exam.get("meta", {})
    for k in REQUIRED_META:
        if not meta.get(k):
            errs.append(f"meta.{k} 누락")
    qs = exam.get("questions", [])
    if not qs:
        errs.append("questions 비어 있음")
    seen = set()
    for q in qs:
        no = q.get("no")
        for k in REQUIRED_Q:
            if q.get(k) in (None, ""):
                errs.append(f"문항 {no}: {k} 누락")
        if no in seen:
            errs.append(f"문항번호 중복: {no}")
        seen.add(no)
        if q.get("type") == "객관식" and q_choices(q) < 4:
            errs.append(f"문항 {no}: 객관식인데 선지 {q_choices(q)}개")
        if not any(b["t"] == "text" and b.get("text") for b in q.get("blocks") or []):
            errs.append(f"문항 {no}: 발문(text 블록) 없음")
        for im in q_images(q):
            if not im.get("file"):
                errs.append(f"문항 {no}: 이미지 file 누락")
        alignment = q.get("alignment")
        if alignment and alignment.get("status") not in (None, "unreviewed"):
            try:
                from .profile import validate_alignment
                for err in validate_alignment(alignment):
                    errs.append(f"문항 {no}: {err}")
            except (KeyError, ValueError) as exc:
                errs.append(f"문항 {no}: 성취기준 검증 실패: {exc}")
    # 번호 연속성
    nos = sorted(seen)
    if nos:
        missing = [n for n in range(nos[0], nos[-1] + 1) if n not in seen]
        if missing:
            errs.append(f"문항번호 결번: {missing}")
    return errs


def stats(exam):
    qs = exam.get("questions", [])
    return {
        "count": len(qs),
        "points_sum": round(sum(q.get("points") or 0 for q in qs), 1),
        "with_images": sum(1 for q in qs if q_images(q)),
        "answered": sum(1 for q in qs if q.get("answer")),
        "analyzed": sum(1 for q in qs if q.get("unit") and q.get("intent")),
        "variants": sum(len(q.get("variants") or []) for q in qs),
    }
