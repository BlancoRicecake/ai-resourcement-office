# -*- coding: utf-8 -*-
"""S3 HWP 생성: exam.json → output/<slug>/시험지_카피.hwp (또는 변형문제지.hwp)

사용:
    python scripts/step3_build_hwp.py --slug 2023-mokdong-1-2final [--mode copy|variant] [--pdf]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import ir
from lib.hwp_writer import build_exam
from lib.variant_quality import blocking_messages, validate_exam_variants

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--mode", choices=["copy", "variant"], default="copy")
    ap.add_argument("--pdf", action="store_true", help="QA용 PDF도 함께 저장")
    args = ap.parse_args()

    wd = os.path.join(ROOT, "work", args.slug)
    exam = ir.load(os.path.join(wd, "exam.json"))
    errs = ir.validate(exam)
    if errs:
        print("exam.json 검증 실패 — 생성 중단:")
        for e in errs:
            print(" -", e)
        sys.exit(1)

    if args.mode == "variant":
        quality_issues = validate_exam_variants(exam, output_gate=True)
        blocks = blocking_messages(quality_issues)
        if blocks:
            print("변형문제 품질 게이트 실패 — 생성 중단:")
            for message in blocks:
                print(" -", message)
            sys.exit(1)
        for issue in quality_issues:
            if issue.get("severity") == "warning":
                print("변형문제 품질 경고:", issue["message"])

    out_dir = os.path.join(ROOT, "output", args.slug)
    name = "시험지_카피" if args.mode == "copy" else "변형문제지"
    out_hwp = os.path.join(out_dir, f"{name}.hwp")
    out_pdf = os.path.join(out_dir, f"{name}.pdf") if args.pdf else None

    ok = build_exam(exam, out_hwp, asset_dir=wd, mode=args.mode, pdf_also=out_pdf)
    print(f"saved={ok}: {out_hwp}")
    if out_pdf:
        print(f"pdf: {out_pdf}")
    print("stats:", ir.stats(exam))


if __name__ == "__main__":
    main()
