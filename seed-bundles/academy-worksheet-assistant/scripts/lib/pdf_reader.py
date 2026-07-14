# -*- coding: utf-8 -*-
"""PyMuPDF 래퍼: 시험지 PDF에서 텍스트(단 인식) + 그림 영역을 추출한다.

산출:
  - 텍스트 라인: 단(column) 정렬 순서로, 첨자 마크업(H_{2}O) 복원 시도
  - 그림: 임베디드 이미지 rect + 벡터 드로잉 클러스터를 병합한 영역을
          페이지에서 클립 렌더링(WYSIWYG — 라벨 텍스트 포함)하여 PNG 저장
  - 페이지 전체 렌더 PNG (에이전트 검토용)
"""
import os

import fitz

RENDER_DPI = 200
CLIP_DPI = 220
# 벡터 드로잉을 그림 후보로 볼 최소 크기 (pt)
MIN_DRAW_W, MIN_DRAW_H = 15.0, 8.0
# rect 병합 간격 (pt): 이 거리 안이면 같은 그림으로 본다
MERGE_GAP = 8.0


def _rects_close(a, b, gap=MERGE_GAP):
    ea = fitz.Rect(a.x0 - gap, a.y0 - gap, a.x1 + gap, a.y1 + gap)
    return ea.intersects(b)


def _merge_rects(rects, gap=MERGE_GAP):
    """서로 겹치거나 gap 이내로 인접한 rect들을 병합 클러스터로 만든다."""
    rects = [fitz.Rect(r) for r in rects]
    changed = True
    while changed:
        changed = False
        out = []
        while rects:
            cur = rects.pop()
            merged = False
            for i, o in enumerate(out):
                if _rects_close(cur, o, gap):
                    out[i] = o | cur
                    merged = True
                    changed = True
                    break
            if not merged:
                out.append(cur)
        rects = out
        if not changed:
            return rects
    return rects


def _line_to_markup(line, body_size):
    """스팬 크기/기준선 오프셋으로 아래·위첨자를 _{ } ^{ } 마크업으로 복원."""
    parts = []
    spans = line.get("spans", [])
    if not spans:
        return ""
    sizes = [s["size"] for s in spans]
    ref = max(sizes)  # 라인 내 기준 크기
    base_y = None
    for s in spans:
        if s["size"] >= ref * 0.9:
            base_y = s["origin"][1]
            break
    if base_y is None:
        base_y = spans[0]["origin"][1]
    for s in spans:
        t = s["text"]
        if not t:
            continue
        small = s["size"] < ref * 0.78 and s["size"] < body_size * 0.9
        if small and t.strip():
            dy = s["origin"][1] - base_y
            if dy > 0.5:
                parts.append("_{%s}" % t.strip())
            elif dy < -0.5:
                parts.append("^{%s}" % t.strip())
            else:
                parts.append(t)
        else:
            parts.append(t)
    return "".join(parts)


def _page_body_size(page_dict):
    """페이지 본문 대표 글자 크기(최빈값)."""
    from collections import Counter

    c = Counter()
    for b in page_dict["blocks"]:
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                if s["text"].strip():
                    c[round(s["size"], 1)] += len(s["text"])
    return c.most_common(1)[0][0] if c else 10.0


def extract_page(page, page_no, assets_dir, doc):
    """한 페이지에서 텍스트 라인(단 순서)과 그림 영역을 추출한다."""
    pw, ph = page.rect.width, page.rect.height
    mid_x = pw / 2
    pd = page.get_text("dict")
    body_size = _page_body_size(pd)

    # --- 그림 후보 rect 수집 ---
    fig_rects = []
    for img in page.get_images(full=True):
        xref = img[0]
        for r in page.get_image_rects(xref):
            if r.width < 3 or r.height < 3:
                continue
            fig_rects.append(fitz.Rect(r))
    for dr in page.get_drawings():
        r = fitz.Rect(dr["rect"])
        # 전체 페이지 테두리/단 구분 세로선/문항 구분 가로선 제외
        if r.width >= pw * 0.9 or r.height >= ph * 0.85:
            continue
        if r.width < MIN_DRAW_W and r.height < MIN_DRAW_H:
            continue
        # 극단적으로 가늘고 긴 선(구분선)은 제외
        if (r.height < 2 and r.width > 100) or (r.width < 2 and r.height > 100):
            continue
        fig_rects.append(r)
    merged = _merge_rects(fig_rects)

    # 표/보기 박스 등 순수 괘선일 수도 있으므로 일단 모두 저장하고
    # 검토 단계(S2)에서 에이전트가 role/소속을 판정한다.
    images = []
    for i, r in enumerate(sorted(merged, key=lambda r: (r.x0 > mid_x, r.y0)), 1):
        clip = fitz.Rect(
            max(r.x0 - 2, 0), max(r.y0 - 2, 0), min(r.x1 + 2, pw), min(r.y1 + 2, ph)
        )
        if clip.width < 8 or clip.height < 8:
            continue
        pix = page.get_pixmap(clip=clip, dpi=CLIP_DPI)
        fname = f"p{page_no}_fig{i}.png"
        pix.save(os.path.join(assets_dir, fname))
        images.append(
            {
                "file": f"assets/{fname}",
                "page": page_no,
                "bbox": [round(v, 1) for v in clip],
                "column": 1 if (clip.x0 + clip.x1) / 2 > mid_x else 0,
                "width_pt": round(clip.width, 1),
                "height_pt": round(clip.height, 1),
            }
        )

    # --- 텍스트 라인 (단 순서 정렬) ---
    lines = []
    for b in pd["blocks"]:
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            text = _line_to_markup(l, body_size)
            if not text.strip():
                continue
            bbox = l["bbox"]
            col = 1 if (bbox[0] + bbox[2]) / 2 > mid_x else 0
            lines.append(
                {
                    "text": text,
                    "bbox": [round(v, 1) for v in bbox],
                    "column": col,
                }
            )
    lines.sort(key=lambda x: (x["column"], x["bbox"][1], x["bbox"][0]))

    return {
        "page": page_no,
        "width": round(pw, 1),
        "height": round(ph, 1),
        "lines": lines,
        "images": images,
    }


def extract_pdf(pdf_path, out_dir):
    """PDF 전체를 추출해 dict(extract.json 내용)로 반환하고 assets/pages를 저장."""
    assets_dir = os.path.join(out_dir, "assets")
    pages_dir = os.path.join(out_dir, "pages")
    os.makedirs(assets_dir, exist_ok=True)
    os.makedirs(pages_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    result = {
        "source_pdf": os.path.abspath(pdf_path),
        "page_count": doc.page_count,
        "has_text": False,
        "pages": [],
    }
    for i, page in enumerate(doc, 1):
        page.get_pixmap(dpi=RENDER_DPI).save(
            os.path.join(pages_dir, f"page{i}.png")
        )
        pr = extract_page(page, i, assets_dir, doc)
        if pr["lines"]:
            result["has_text"] = True
        result["pages"].append(pr)
    doc.close()
    return result
