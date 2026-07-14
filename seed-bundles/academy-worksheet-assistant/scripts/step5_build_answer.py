# -*- coding: utf-8 -*-
"""S8 정답 및 해설지 생성: exam.json → output/<slug>/정답및해설지.hwp

구성: 원문항 정답표 → 원문항 해설 → (변형이 있으면) 변형 정답표 → 변형 해설

사용:
    python scripts/step5_build_answer.py --slug 2023-mokdong-1-2final [--pdf]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import ir
from lib.hwp_writer import ExamWriter
from lib.variant_quality import blocking_messages, validate_exam_variants

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def answer_grid_lines(pairs, per_line=8):
    """[(표시번호, 정답)] → '1.② 2.⑤ ...' 행 목록."""
    out = []
    for i in range(0, len(pairs), per_line):
        chunk = pairs[i : i + per_line]
        out.append("   ".join(f"{n}.{a or '?'}" for n, a in chunk))
    return out


def write_explanations(w, items):
    """items: [(표시번호, 배점, unit, intent, answer, explanation)]"""
    for no, pts, unit, intent, ans, expl in items:
        head = f"{no}. 정답 {ans or '?'}"
        if pts is not None:
            p = int(pts) if float(pts).is_integer() else pts
            head += f" ({p}점)"
        if unit:
            head += f"  [{unit.get('중단원', '')} | {unit.get('성취기준', '')}]"
        w.para(head, bold=True)
        if intent:
            w.para(f"◦ 출제 의도: {intent}")
        if expl:
            w.para(f"◦ 해설: {expl}")
        w.para()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument(
        "--variant-only",
        action="store_true",
        help="원문항 정답·해설을 제외하고 변형문항 정답·해설만 생성",
    )
    args = ap.parse_args()

    wd = os.path.join(ROOT, "work", args.slug)
    exam = ir.load(os.path.join(wd, "exam.json"))
    errs = ir.validate(exam)
    if errs:
        print("exam.json 검증 실패 — 생성 중단:")
        for error in errs:
            print(" -", error)
        sys.exit(1)
    meta = exam["meta"]
    qs = exam["questions"]

    out_dir = os.path.join(ROOT, "output", args.slug)
    answer_name = "변형문제_정답및해설.hwp" if args.variant_only else "정답및해설지.hwp"
    out_hwp = os.path.join(out_dir, answer_name)

    # 변형 문항 수집 (변형문제지의 표시 번호와 동일하게 순번 부여)
    variants = []
    vno = 0
    for q in qs:
        for v in q.get("variants") or []:
            vno += 1
            variants.append((vno, q, v))

    if variants:
        quality_issues = validate_exam_variants(exam, output_gate=True)
        blocks = blocking_messages(quality_issues)
        if blocks:
            print("변형문제 품질 게이트 실패 — 해설지 생성 중단:")
            for message in blocks:
                print(" -", message)
            sys.exit(1)

    w = ExamWriter(visible=False)
    try:
        w.page_setup()
        w.base_font()
        w.title_block(
            f"{meta['subject']} — {'변형문제 ' if args.variant_only else ''}정답 및 해설",
            f"{meta['year']}학년도 {meta['school']} {meta['grade']}학년 {meta['term']}",
            "변형문제 전용 교사용 검토본" if args.variant_only else "기출 카피본 + 변형문제 해설",
        )
        w.two_columns()

        if not args.variant_only:
            w.para("■ 원문항 정답표", bold=True, pt=11)
            for line in answer_grid_lines([(q["no"], q.get("answer")) for q in qs], per_line=5):
                w.para(line)
            w.para()
            w.para("■ 원문항 해설", bold=True, pt=11)
            w.para()
            write_explanations(
                w,
                [
                    (q["no"], q.get("points"), q.get("unit"), q.get("intent"), q.get("answer"), q.get("explanation"))
                    for q in qs
                ],
            )

        if variants:
            w.para("■ 변형문항 정답표 (변형문제지 번호 기준)", bold=True, pt=11)
            for line in answer_grid_lines([(n, v.get("answer")) for n, _, v in variants], per_line=5):
                w.para(line)
            w.para()
            w.para("■ 변형문항 해설", bold=True, pt=11)
            w.para()
            write_explanations(
                w,
                [
                    (
                        f"{n} (원 {q['no']}번 변형)",
                        v.get("points", q.get("points")),
                        q.get("unit"),
                        None,
                        v.get("answer"),
                        (v.get("explanation") or "")
                        + (
                            f"  [변형: {v['change_note']}]"
                            if v.get("change_note") and not args.variant_only
                            else ""
                        ),
                    )
                    for n, q, v in variants
                ],
            )

        ok = w.save(out_hwp)
        if args.pdf:
            pdf_name = "변형문제_정답및해설.pdf" if args.variant_only else "정답및해설지.pdf"
            w.save_pdf(os.path.join(out_dir, pdf_name))
    finally:
        w.quit()

    print(f"saved={ok}: {out_hwp}")
    original_count = 0 if args.variant_only else len(qs)
    print(f"원문항 {original_count}개 / 변형 {len(variants)}개 해설 수록")


if __name__ == "__main__":
    main()
