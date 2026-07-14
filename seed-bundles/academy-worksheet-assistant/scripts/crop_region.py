# -*- coding: utf-8 -*-
"""수동 크롭 유틸: 원본 PDF의 지정 영역을 assets/ PNG로 저장하고
exam.json에서 file=null인 이미지 블록을 채운다.

bbox는 pages/pageN.png 렌더(기본 dpi 200) 픽셀 좌표로 받는다.

사용:
    python scripts/crop_region.py --slug <slug> --qno 11 --page 3 --bbox 74 1027 772 1158
"""
import argparse
import os
import sys

import fitz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import ir

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER_DPI = 200


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--qno", type=int, required=True)
    ap.add_argument("--page", type=int, required=True)
    ap.add_argument("--bbox", type=float, nargs=4, required=True, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--dpi", type=int, default=RENDER_DPI, help="bbox 좌표의 렌더 dpi")
    args = ap.parse_args()

    wd = os.path.join(ROOT, "work", args.slug)
    exam = ir.load(os.path.join(wd, "exam.json"))

    scale = 72.0 / args.dpi
    rect = fitz.Rect(*[v * scale for v in args.bbox])

    doc = fitz.open(exam["meta"]["source_pdf"])
    page = doc[args.page - 1]
    pix = page.get_pixmap(clip=rect, dpi=220)
    fname = f"p{args.page}_manual_q{args.qno}.png"
    out_png = os.path.join(wd, "assets", fname)
    pix.save(out_png)
    doc.close()

    q = next(q for q in exam["questions"] if q["no"] == args.qno)
    filled = False
    for b in q["blocks"]:
        if b["t"] == "image" and not b.get("file"):
            b["file"] = f"assets/{fname}"
            b["width_pt"] = round(rect.width, 1)
            b["height_pt"] = round(rect.height, 1)
            b["assoc_confidence"] = "manual"
            b.pop("note", None)
            b.pop("bbox_hint", None)
            filled = True
            break
    if not filled:
        print("경고: file=null 이미지 블록이 없어 exam.json은 수정하지 않음")
    else:
        ir.save(exam, os.path.join(wd, "exam.json"))
        print(f"OK: Q{args.qno} <- assets/{fname} ({rect.width:.0f}x{rect.height:.0f}pt)")
    print(f"png: {out_png}")


if __name__ == "__main__":
    main()
