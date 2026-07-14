# -*- coding: utf-8 -*-
"""S1 추출: 시험지 PDF → work/<slug>/extract.json + assets/ + pages/

사용:
    python scripts/step1_extract.py --pdf "경로.pdf" --slug 2023-목동중-1-2기말
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.pdf_reader import extract_pdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--slug", required=True, help="work/ 하위 작업 폴더명")
    ap.add_argument("--name", default="extract.json", help="산출 json 파일명")
    args = ap.parse_args()

    out_dir = os.path.join(ROOT, "work", args.slug)
    os.makedirs(out_dir, exist_ok=True)
    result = extract_pdf(args.pdf, out_dir)

    out_path = os.path.join(out_dir, args.name)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    n_lines = sum(len(p["lines"]) for p in result["pages"])
    n_imgs = sum(len(p["images"]) for p in result["pages"])
    print(f"OK: {out_path}")
    print(f"pages={result['page_count']} text_lines={n_lines} fig_regions={n_imgs} has_text={result['has_text']}")


if __name__ == "__main__":
    main()
