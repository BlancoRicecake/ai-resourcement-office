# -*- coding: utf-8 -*-
"""S2 정규화: exam_draft.json → exam.json + review/01_카피검토.md

문항별 rows/images를 y순서 블록 흐름으로 재구성한다:
  text / image / passage(<보기>) / choices / choice_table

이후 에이전트가 페이지 렌더와 대조 검토하고 exam.json을 직접 교정한다.

사용:
    python scripts/step2b_normalize.py --slug 2026-example-midterm --term "1학기 중간"
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import ir
from lib.profile import empty_alignment, load_profile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

POINTS = re.compile(r"\(\s*(\d+(?:\.\d+)?)\s*점\s*\)")
MARK = re.compile(r"([①②③④⑤])")
BOGI = re.compile(r"^\s*<\s*보\s*기\s*>\s*$")


def row_text(row):
    return "  ".join(c for c in row["cells"] if c.strip())


def flow_items(q):
    """rows와 images를 (page, column, y) 순서의 단일 흐름으로 병합."""
    items = [("row", r["page"], r["column"], r["y"], r) for r in q["rows"]]
    for im in q["images"]:
        items.append(("img", im["page"], im["column"], im["bbox"][1], im))
    items.sort(key=lambda t: (t[1], t[2], t[3]))
    return items


def parse_question(q):
    """한 문항의 흐름을 블록 리스트로 변환."""
    blocks = []
    points = None
    state = "stem"  # stem | passage | choices
    text_buf = []
    passage_buf = []
    choice_rows = []
    header_row = None   # 표형 선지 헤더로 확정된 행
    pending_row = None  # 헤더 후보(다음 행이 선지면 헤더로 승격)

    def flush_text():
        nonlocal text_buf
        t = re.sub(r"\s+", " ", " ".join(text_buf)).strip()
        if t:
            blocks.append({"t": "text", "text": t})
        text_buf = []

    def flush_pending_to_text():
        nonlocal pending_row
        if pending_row is not None:
            text_buf.append(row_text(pending_row))
            pending_row = None

    def flush_passage():
        nonlocal passage_buf
        if passage_buf:
            blocks.append({"t": "passage", "lines": passage_buf})
            passage_buf = []

    def flush_choices():
        nonlocal choice_rows, header_row
        if not choice_rows:
            header_row = None
            return
        multi_cell = [
            r for r in choice_rows if len([c for c in r["cells"] if c.strip()]) >= 3
        ]
        if len(multi_cell) >= 3 and header_row is not None:
            headers = [c for c in header_row["cells"] if c.strip()]
            rows = []
            for r in choice_rows:
                cells = [c for c in r["cells"] if c.strip()]
                if cells and MARK.match(cells[0]):
                    rows.append(cells[1:])
                elif rows:
                    rows[-1] = rows[-1] + cells
            blocks.append({"t": "choice_table", "headers": headers, "rows": rows})
        else:
            joined = " ".join(row_text(r) for r in choice_rows)
            parts = MARK.split(joined)
            choices = []
            i = 1
            while i < len(parts) - 1:
                choices.append((parts[i] + " " + parts[i + 1].strip()).strip())
                i += 2
            if choices:
                blocks.append({"t": "choices", "items": choices})
        choice_rows = []
        header_row = None

    for kind, page, col, y, obj in flow_items(q):
        if kind == "img":
            flush_pending_to_text()
            if state == "stem":
                flush_text()
            elif state == "passage":
                flush_passage()
            elif state == "choices":
                flush_choices()
                state = "stem"
            blocks.append(
                {
                    "t": "image",
                    "file": obj["file"],
                    "width_pt": obj["width_pt"],
                    "height_pt": obj["height_pt"],
                    "assoc_confidence": obj.get("assoc_confidence", "high"),
                }
            )
            continue

        text = row_text(obj)
        m = POINTS.search(text)
        if m and points is None:
            points = float(m.group(1))
            text = POINTS.sub("", text).strip()
            obj = dict(obj, cells=[POINTS.sub("", c).strip() for c in obj["cells"]])
            if not text:
                continue

        if BOGI.match(text):
            flush_pending_to_text()
            flush_text()
            flush_choices()
            state = "passage"
            continue

        if MARK.search(text):
            if state == "stem":
                # 보류 중인 행이 있으면 표형 선지 헤더로 승격
                if pending_row is not None:
                    header_row = pending_row
                    pending_row = None
                flush_text()
            elif state == "passage":
                flush_passage()
            state = "choices"
            choice_rows.append(obj)
            continue

        if state == "choices":
            # 마커 없는 행이 선지 뒤에 오면: 선지 이어짐(줄바꿈) 취급
            choice_rows.append(obj)
        elif state == "passage":
            passage_buf.append(text)
        else:
            flush_pending_to_text()
            cells = [c for c in obj["cells"] if c.strip()]
            if len(cells) >= 2 and all(len(c) <= 14 for c in cells):
                pending_row = obj  # 표형 선지 헤더 후보
            else:
                text_buf.append(text)

    flush_pending_to_text()
    flush_text()
    flush_passage()
    flush_choices()

    q_type = "객관식" if any(b["t"] in ("choices", "choice_table") for b in blocks) else "서술형"
    return {
        "no": q["no"],
        "points": points,
        "type": q_type,
        "blocks": blocks,
        "answer": None,
        "answer_source": None,
        "unit": None,
        "intent": None,
        "alignment": empty_alignment(),
        "explanation": None,
        "variants": [],
    }


def strip_qnum(question):
    """첫 text 블록 앞의 '12.' 문항번호를 제거(빌더가 다시 붙임)."""
    for b in question["blocks"]:
        if b["t"] == "text":
            b["text"] = re.sub(r"^\s*\d{1,2}\s*\.\s*", "", b["text"], count=1)
            break
    return question


def render_review(exam, wd):
    lines = ["# 01 카피 검토 (S2 정규화 결과)", ""]
    st = ir.stats(exam)
    lines.append(
        f"- 문항 수: **{st['count']}** / 배점 합계: **{st['points_sum']}** / 그림 포함 문항: {st['with_images']}"
    )
    lines.append(f"- 페이지 렌더: `pages/page1.png` ~ — 원본과 반드시 대조할 것")
    lines.append("")
    for q in exam["questions"]:
        lines.append(f"## Q{q['no']} ({q['points']}점, {q['type']})")
        for b in q["blocks"]:
            if b["t"] == "text":
                lines.append(f"- {b['text']}")
            elif b["t"] == "image":
                lines.append(f"- 🖼 `{b['file']}` ({b['width_pt']}x{b['height_pt']}pt, {b['assoc_confidence']})")
            elif b["t"] == "passage":
                lines.append("- <보기>")
                for pl in b["lines"]:
                    lines.append(f"    - {pl}")
            elif b["t"] == "choices":
                for c in b["items"]:
                    lines.append(f"    - {c}")
            elif b["t"] == "choice_table":
                lines.append(f"    - [표형 선지] 헤더: {b['headers']}")
                for i, r in enumerate(b["rows"], 1):
                    lines.append(f"    - {'①②③④⑤'[i-1]} {r}")
        lines.append("")
    out = os.path.join(wd, "review", "01_카피검토.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--school")
    ap.add_argument("--year")
    ap.add_argument("--grade")
    ap.add_argument("--term", required=True)
    ap.add_argument("--subject")
    ap.add_argument("--publisher", help="교과서 출판사(미입력 시 국가 교육과정만 확정)")
    ap.add_argument("--textbook-title", help="교과서 정확한 서명")
    ap.add_argument("--exam-scope", help="학교가 고지한 시험범위 원문")
    args = ap.parse_args()

    wd = os.path.join(ROOT, "work", args.slug)
    draft = json.load(open(os.path.join(wd, "exam_draft.json"), encoding="utf-8"))

    try:
        profile = load_profile()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    school = args.school or profile.get("default_school")
    year = args.year or profile.get("exam_year")
    grade = args.grade or profile.get("grade")
    subject = args.subject or profile.get("subject")
    if not all((school, year, grade, subject, args.term)):
        raise SystemExit("school/year/grade/subject/term이 필요합니다. setup.py 설정 또는 CLI 인자를 확인하세요.")
    publisher = args.publisher or profile.get("publisher")
    textbook_title = args.textbook_title or profile.get("textbook_title")
    scope = {
        "curriculum": {
            "name": profile.get("curriculum"),
            "source": profile.get("curriculum_source"),
            "knowledge_status": profile.get("knowledge_status", "pending"),
        },
        "textbook": {"publisher": publisher, "title": textbook_title, "mapping_status": "user_provided" if publisher else "not_provided"},
        "exam": {"raw_scope": args.exam_scope, "confirmed_unit_codes": [], "confirmed_standard_codes": [], "status": "unconfirmed"},
    }
    exam = {
        "meta": {
            "school": school,
            "year": year,
            "grade": grade,
            "term": args.term,
            "subject": subject,
            "source_pdf": draft["meta"]["source_pdf"],
            "curriculum": profile.get("curriculum"),
            "curriculum_resolution": None,
            "scope": scope,
            "variant_quality_mode": "strict" if profile.get("knowledge_status") == "ready" else "locked",
        },
        "questions": [strip_qnum(parse_question(q)) for q in draft["questions"]],
    }

    out = os.path.join(wd, "exam.json")
    ir.save(exam, out)
    errs = ir.validate(exam)
    review = render_review(exam, wd)
    print(f"OK: {out}")
    print(f"review: {review}")
    print("stats:", ir.stats(exam))
    if errs:
        print("검증 경고:")
        for e in errs:
            print(" -", e)


if __name__ == "__main__":
    main()
