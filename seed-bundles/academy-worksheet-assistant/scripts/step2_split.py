# -*- coding: utf-8 -*-
"""S2 문항 분할(결정론 파트): extract.json → exam_draft.json

머리글/꼬리말을 걸러내고, 같은 y의 조각을 행으로 묶은 뒤 문항번호로 분할한다.
안내문("1. 학년, 반, ...")처럼 문항번호를 흉내내는 행이 있으므로,
후보 시작점들로 1..N 체인을 여러 개 만들어 "(N점)" 배점 패턴을 가장 많이
포함하는 체인을 채택한다. 그림은 (페이지, 단, y범위) 기준으로 문항에 귀속.
결과는 초안이며, 에이전트가 검토·교정해 exam.json으로 확정한다.

사용:
    python scripts/step2_split.py --slug 2023-mokdong-1-2final
"""
import argparse
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Q_START = re.compile(r"^\s*(\d{1,2})\s*\.\s+\S")
POINTS = re.compile(r"\(\s*(\d+(?:\.\d+)?)\s*점\s*\)")
FOOTER_PAT = re.compile(r"^-{10,}|총\s*\(\s*\d+\s*\)\s*쪽|저작권|무단전송|다음 쪽에 계속")
ARTIFACT = re.compile(r"^[`·\s]+$")


def group_rows(lines, y_tol=3.5):
    """같은 단에서 y가 근접한 라인 조각들을 하나의 행으로 묶는다(이미 정렬됨)."""
    rows = []
    for l in lines:
        if ARTIFACT.match(l["text"]):
            continue
        if rows:
            r = rows[-1]
            if l["column"] == r["column"] and abs(l["bbox"][1] - r["y"]) <= y_tol:
                r["cells"].append(l["text"].strip())
                continue
        rows.append(
            {"column": l["column"], "y": l["bbox"][1], "cells": [l["text"].strip()]}
        )
    return rows


def collect_rows(extract):
    """전 페이지 행을 읽기 순서(페이지→단→y)의 평면 리스트로 만든다."""
    flat = []
    for p in extract["pages"]:
        for row in group_rows(p["lines"]):
            text = "  ".join(row["cells"])
            # 꼬리말은 패턴으로만 거른다 (y 컷은 꼬리말 없는 문서의 본문을 삭제함)
            if FOOTER_PAT.search(text):
                continue
            flat.append(
                {
                    "page": p["page"],
                    "column": row["column"],
                    "y": round(row["y"], 1),
                    "cells": row["cells"],
                    "text": text,
                }
            )
    return flat


def pick_chain(flat):
    """문항 시작 후보들로 1..N 체인들을 만들고 배점 패턴 점수가 최고인 체인 선택."""
    cands = []  # (flat_idx, number)
    for i, row in enumerate(flat):
        m = Q_START.match(row["text"])
        if m:
            cands.append((i, int(m.group(1))))

    chains = []
    for s, (idx, num) in enumerate(cands):
        if num != 1:
            continue
        chain = [(idx, 1)]
        want = 2
        for j in range(s + 1, len(cands)):
            if cands[j][1] == want and cands[j][0] > chain[-1][0]:
                chain.append(cands[j])
                want += 1
        chains.append(chain)

    if not chains:
        return []

    def score(chain):
        pts = 0
        for k, (idx, num) in enumerate(chain):
            end = chain[k + 1][0] if k + 1 < len(chain) else len(flat)
            body = " ".join(flat[i]["text"] for i in range(idx, end))
            if POINTS.search(body):
                pts += 1
        return (len(chain), pts)

    return max(chains, key=score)


def split_questions(extract):
    flat = collect_rows(extract)
    chain = pick_chain(flat)
    if not chain:
        raise SystemExit("문항 시작을 찾지 못함")

    starts = {idx: num for idx, num in chain}
    questions = {}
    header_rows = []
    cur = None
    for i, row in enumerate(flat):
        if i in starts:
            cur = starts[i]
            questions[cur] = {"no": cur, "rows": [], "images": [], "pages": set()}
        if cur is None:
            header_rows.append(row)
            continue
        q = questions[cur]
        q["rows"].append(row)
        q["pages"].add(row["page"])

    # 그림 귀속: 단 안에서 그림 중심 y 직전에 시작한 문항 소속
    order = sorted(questions)
    for p in extract["pages"]:
        page_no = p["page"]
        q_starts = {}  # (column) -> [(y, qno)]
        for qno in order:
            rows = [r for r in questions[qno]["rows"] if r["page"] == page_no]
            if rows:
                first = rows[0]
                q_starts.setdefault(first["column"], []).append((first["y"], qno))
        for im in p["images"]:
            col = im["column"]
            cy = (im["bbox"][1] + im["bbox"][3]) / 2
            owner = None
            for y, qno in sorted(q_starts.get(col, [])):
                if y <= cy + 2:
                    owner = qno
                else:
                    break
            if owner is None:
                # 단의 첫 문항보다 위 → 이전 단/페이지에서 이어진 문항
                later = [qno for _, qno in sorted(q_starts.get(col, []))]
                prev_qs = [q for q in order if not later or q < later[0]]
                # 이 페이지에 걸쳐 있는 문항 중 가장 이른 것 이전의 마지막 문항
                page_qs = [q for q in order if page_no in questions[q]["pages"]]
                cands = [q for q in prev_qs if q in page_qs]
                owner = cands[0] if cands else None
            entry = dict(im)
            entry["assoc_confidence"] = "high" if owner else "low"
            if owner:
                questions[owner]["images"].append(entry)
            else:
                header_rows.append({"page": page_no, "unassigned_image": entry})

    for q in questions.values():
        q["pages"] = sorted(q["pages"])
    return questions, order, header_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    args = ap.parse_args()

    wd = os.path.join(ROOT, "work", args.slug)
    extract = json.load(open(os.path.join(wd, "extract.json"), encoding="utf-8"))
    questions, order, header_rows = split_questions(extract)

    draft = {
        "meta": {"source_pdf": extract["source_pdf"], "note": "S2 초안 — 에이전트 교정 필요"},
        "header_rows": header_rows,
        "questions": [questions[n] for n in order],
    }
    out = os.path.join(wd, "exam_draft.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=1)

    print(f"OK: {out}")
    print(f"questions={len(order)} first..last={order[0]}..{order[-1]}")
    missing = [n for n in range(1, order[-1] + 1) if n not in questions]
    print("결번:", missing if missing else "없음")
    n_img = sum(len(q["images"]) for q in questions.values())
    print(f"문항 귀속 그림 수: {n_img}")
    for q in draft["questions"]:
        joined = " ".join(" ".join(r["cells"]) for r in q["rows"])
        m = POINTS.search(joined)
        print(
            f"  Q{q['no']:>2} rows={len(q['rows']):>2} imgs={len(q['images'])} "
            f"pages={q['pages']} points={m.group(1) if m else None}"
        )


if __name__ == "__main__":
    main()
