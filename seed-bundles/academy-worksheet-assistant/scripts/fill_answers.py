# -*- coding: utf-8 -*-
"""정답 기입: "no:배점:정답" 목록을 exam.json에 채우고 배점 교차검증한다.

사용:
    python scripts/fill_answers.py --slug <slug> --source 정답pdf --data "1:3:2,2:3:5,..."
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import ir

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKS = {"1": "①", "2": "②", "3": "③", "4": "④", "5": "⑤"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--source", required=True, choices=["정답pdf", "비전판독", "사람확인"])
    ap.add_argument("--data", required=True, help="no:배점:정답 콤마 구분")
    args = ap.parse_args()

    path = os.path.join(ROOT, "work", args.slug, "exam.json")
    exam = ir.load(path)
    qmap = {q["no"]: q for q in exam["questions"]}

    mismatches = []
    filled = 0
    for item in args.data.split(","):
        no_s, pts_s, ans_s = item.strip().split(":")
        no, pts = int(no_s), float(pts_s)
        q = qmap.get(no)
        if q is None:
            mismatches.append(f"Q{no}: exam.json에 없음")
            continue
        if q.get("points") != pts:
            mismatches.append(f"Q{no}: 배점 불일치 exam={q.get('points')} vs 정답지={pts}")
        q["answer"] = MARKS.get(ans_s, ans_s)
        q["answer_source"] = args.source
        filled += 1

    missing = [q["no"] for q in exam["questions"] if not q.get("answer")]
    ir.save(exam, path)
    print(f"OK: {filled}개 기입, 정답 없는 문항: {missing if missing else '없음'}")
    if mismatches:
        print("배점 교차검증 불일치:")
        for m in mismatches:
            print(" -", m)
    else:
        print("배점 교차검증: 전 문항 일치")


if __name__ == "__main__":
    main()
