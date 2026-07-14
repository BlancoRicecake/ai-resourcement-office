# -*- coding: utf-8 -*-
"""변형문제 품질 게이트를 HWP 생성 없이 실행한다."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import ir
from lib.variant_quality import validate_exam_variants

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--output-gate", action="store_true", help="qa.status=pass까지 출고 기준으로 검사")
    args = ap.parse_args()
    path = os.path.join(ROOT, "work", args.slug, "exam.json")
    exam = ir.load(path)
    issues = validate_exam_variants(exam, output_gate=args.output_gate)
    errors = [x for x in issues if x["severity"] == "error"]
    warnings = [x for x in issues if x["severity"] == "warning"]
    print(f"variants={sum(len(q.get('variants') or []) for q in exam.get('questions') or [])}")
    print(f"errors={len(errors)} warnings={len(warnings)}")
    for issue in issues:
        print(f"[{issue['severity'].upper()}] {issue['code']}: {issue['message']}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
