# -*- coding: utf-8 -*-
"""S4 카피 검수: 카피 HWP의 PDF를 재추출해 원본 exam.json과 문항별 대조.

검사 항목: 문항 수 / 문항 번호 / 배점 / 텍스트 유사도(공백 정규화 difflib).
그림은 exam.json의 파일을 그대로 임베드하므로 개수만 참고 표기.

사용:
    python scripts/step4_qa.py --slug 2023-mokdong-1-2final
"""
import argparse
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import ir
from lib.pdf_reader import extract_pdf
from step2_split import split_questions, POINTS
from step2b_normalize import parse_question, strip_qnum

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SIM_WARN = 0.93


def norm(s):
    s = re.sub(r"\[그림[^\]]*\]", "", s)
    s = re.sub(r"[\s`·⬝•・]+", "", s)
    s = s.replace("–", "-").replace("―", "-").replace("—", "-")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--name", default="시험지_카피")
    args = ap.parse_args()

    wd = os.path.join(ROOT, "work", args.slug)
    copy_pdf = os.path.join(ROOT, "output", args.slug, f"{args.name}.pdf")
    if not os.path.exists(copy_pdf):
        sys.exit(f"카피 PDF 없음: {copy_pdf} — step3를 --pdf로 먼저 실행")

    orig = ir.load(os.path.join(wd, "exam.json"))

    qa_dir = os.path.join(wd, "qa_copy")
    extract = extract_pdf(copy_pdf, qa_dir)
    questions, order, _ = split_questions(extract)
    copy_qs = {}
    for n in order:
        cq = strip_qnum(parse_question(questions[n]))
        copy_qs[n] = cq

    lines = [f"# 03 카피 QA 리포트 — {args.slug}", ""]
    problems = []
    orig_nos = [q["no"] for q in orig["questions"]]
    if orig_nos != order:
        problems.append(f"문항 번호 불일치: 원본 {len(orig_nos)}개 vs 카피 {len(order)}개")

    pts_o = sum(q.get("points") or 0 for q in orig["questions"])
    pts_c = sum(copy_qs[n].get("points") or 0 for n in order)
    lines.append(f"- 문항 수: 원본 {len(orig_nos)} / 카피 {len(order)}")
    lines.append(f"- 배점 합계: 원본 {pts_o} / 카피 {pts_c}")
    lines.append("")
    lines.append("| Q | 배점 | 유사도 | 판정 |")
    lines.append("|---|------|--------|------|")

    for q in orig["questions"]:
        n = q["no"]
        c = copy_qs.get(n)
        if c is None:
            problems.append(f"Q{n}: 카피에서 누락")
            lines.append(f"| {n} | - | - | ❌ 누락 |")
            continue
        pt_ok = (q.get("points") == c.get("points"))
        sim = difflib.SequenceMatcher(None, norm(ir.q_text(q)), norm(ir.q_text(c))).ratio()
        flag = "✅"
        if not pt_ok:
            flag = "❌ 배점"
            problems.append(f"Q{n}: 배점 {q.get('points')} vs {c.get('points')}")
        if sim < SIM_WARN:
            flag = f"⚠️ 유사도 {sim:.2f}"
            problems.append(f"Q{n}: 텍스트 유사도 {sim:.2f}")
        lines.append(f"| {n} | {q.get('points')} | {sim:.3f} | {flag} |")

    lines.append("")
    if problems:
        lines.append("## 확인 필요")
        lines += [f"- {p}" for p in problems]
    else:
        lines.append("**전 항목 통과** — 사람 스팟체크(무작위 5문항)만 남음")

    out = os.path.join(wd, "review", "03_QA리포트.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"OK: {out}")
    print(f"problems: {len(problems)}")
    for p in problems[:20]:
        print(" -", p)


if __name__ == "__main__":
    main()
