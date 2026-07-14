# -*- coding: utf-8 -*-
"""pyhwpx 기반 HWP 조립기: exam.json 블록 → 학원 표준 서식 시험지/해설지.

문서 구조: A4 세로, 제목 블록(1단) → 2단(구분선) 본문 → 문항 블록 순차 삽입.
첨자 마크업 H_{2}O / m/s^{2} 는 CharShape 아래·위첨자로 렌더링한다.
COM 수칙: new=True(잔존 ROT 무시), 원자적 열기-조립-저장-종료.
"""
import os
import re
import subprocess

MARKUP = re.compile(r"(_\{[^{}]*\}|\^\{[^{}]*\})")
PT_TO_MM = 0.3528
MAX_IMG_W_MM = 78  # 2단 단폭(~86mm)보다 약간 작게
BODY_FONT = "함초롬바탕"
BODY_PT = 10


def kill_zombie_hwp():
    subprocess.run(["taskkill", "/F", "/IM", "Hwp.exe"], capture_output=True)


class ExamWriter:
    def __init__(self, visible=False):
        kill_zombie_hwp()
        from pyhwpx import Hwp

        self.hwp = Hwp(new=True, visible=visible)

    # ---------- 저수준 ----------
    def text(self, s):
        """마크업(_{ } ^{ })을 첨자로 렌더링하며 텍스트 삽입."""
        for part in MARKUP.split(s):
            if not part:
                continue
            if part.startswith("_{"):
                self.hwp.HAction.Run("CharShapeSubscript")
                self.hwp.insert_text(part[2:-1])
                self.hwp.HAction.Run("CharShapeSubscript")
            elif part.startswith("^{"):
                self.hwp.HAction.Run("CharShapeSuperscript")
                self.hwp.insert_text(part[2:-1])
                self.hwp.HAction.Run("CharShapeSuperscript")
            else:
                self.hwp.insert_text(part)

    def para(self, s="", align=None, bold=False, pt=None, face=None):
        """한 문단 삽입."""
        if align == "center":
            self.hwp.HAction.Run("ParagraphShapeAlignCenter")
        elif align == "left":
            self.hwp.HAction.Run("ParagraphShapeAlignLeft")
        if bold or pt or face:
            self.hwp.set_font(
                Bold=bold, Height=pt or BODY_PT, FaceName=face or BODY_FONT
            )
        self.text(s)
        if bold or pt or face:
            self.hwp.set_font(Bold=False, Height=BODY_PT, FaceName=BODY_FONT)
        self.hwp.insert_text("\r\n")
        if align == "center":
            self.hwp.HAction.Run("ParagraphShapeAlignLeft")

    # ---------- 문서 골격 ----------
    def base_font(self):
        self.hwp.set_font(FaceName=BODY_FONT, Height=BODY_PT)

    def page_setup(self):
        self.hwp.set_pagedef(
            {
                "용지폭": 210,
                "용지길이": 297,
                "위쪽": 15,
                "아래쪽": 15,
                "왼쪽": 15,
                "오른쪽": 15,
                "머리말": 8,
                "꼬리말": 8,
            },
            apply="all",
        )

    def title_block(self, title, subtitle, info_line):
        self.para(title, align="center", bold=True, pt=15)
        self.para(subtitle, align="center", pt=11)
        self.para(info_line, align="center", pt=10)
        self.para("─" * 44, align="center", pt=10)

    def two_columns(self, count=2, gap_mm=8, separator=True):
        # 단 정의 나누기: 제목 블록(1단 전체폭)과 본문(2단)을 같은 페이지에 공존시킨다
        self.hwp.HAction.Run("BreakColDef")
        pset = self.hwp.HParameterSet.HColDef
        self.hwp.HAction.GetDefault("MultiColumn", pset.HSet)
        pset.Count = count
        pset.SameSize = 1
        pset.SameGap = self.hwp.mili_to_hwp_unit(gap_mm)
        if separator:
            pset.LineType = 1  # 실선 구분선
        # ApplyClass/ApplyTo가 없으면 Execute가 False로 조용히 실패한다.
        # ApplyTo=2(현재 다단)여야 BreakColDef 이전(제목)이 1단으로 유지된다.
        pset.HSet.SetItem("ApplyClass", 832)
        pset.HSet.SetItem("ApplyTo", 2)
        ok = self.hwp.HAction.Execute("MultiColumn", pset.HSet)
        if not ok:
            raise RuntimeError("MultiColumn(다단) 적용 실패")

    # ---------- 문항 블록 ----------
    def image(self, path, width_pt, height_pt):
        w = min((width_pt or 100) * PT_TO_MM, MAX_IMG_W_MM)
        ratio = (height_pt or width_pt or 100) / (width_pt or 100)
        h = w * ratio
        self.hwp.HAction.Run("ParagraphShapeAlignCenter")
        self.hwp.insert_picture(
            path, treat_as_char=True, embedded=True, sizeoption=1,
            width=round(w), height=round(h),
        )
        self.hwp.insert_text("\r\n")
        self.hwp.HAction.Run("ParagraphShapeAlignLeft")

    def passage_box(self, lines, label="< 보 기 >"):
        """1x1 표를 <보기> 상자로 사용."""
        self.hwp.create_table(rows=1, cols=1, treat_as_char=True, header=False)
        # 캐럿은 셀 안
        self.hwp.set_font(FaceName=BODY_FONT, Height=BODY_PT)
        self.hwp.HAction.Run("ParagraphShapeAlignCenter")
        self.text(label)
        self.hwp.insert_text("\r\n")
        self.hwp.HAction.Run("ParagraphShapeAlignLeft")
        for i, ln in enumerate(lines):
            self.text(ln)
            if i < len(lines) - 1:
                self.hwp.insert_text("\r\n")
        self.hwp.MoveDocEnd()
        self.hwp.insert_text("\r\n")

    def choices(self, items):
        for c in items:
            self.para("  " + c)

    def choice_table(self, headers, rows):
        # " \t" 조인: 탭 스톱을 넘겨 탭이 무력화돼도 공백 하나는 남아 셀이 붙지 않는다
        marks = "①②③④⑤"
        self.para("\t" + " \t".join(headers))
        for i, r in enumerate(rows):
            mark = marks[i] if i < len(marks) else f"({i+1})"
            self.para("  " + mark + "\t" + " \t".join(str(c) for c in r))

    def column_break(self):
        """현재 다단의 다음 단 맨 위에서 이어 쓴다."""
        self.hwp.HAction.Run("BreakColumn")

    def question(self, q, asset_dir, number=None, points_style="tail"):
        """문항 하나를 블록 순서대로 삽입."""
        no = number if number is not None else q["no"]
        pts = q.get("points")
        blocks = list(q["blocks"])
        # 문항번호가 항상 첫 줄에 오도록: 첫 text 블록보다 앞에 있는 블록은 그 뒤로 보낸다
        first_text = next((i for i, b in enumerate(blocks) if b["t"] == "text"), None)
        if first_text is not None and first_text > 0:
            blocks = [blocks[first_text]] + blocks[:first_text] + blocks[first_text + 1:]

        # 배점을 붙일 text 블록: 첫 선지/보기 이전의 마지막 text 블록
        pts_idx = None
        for i, b in enumerate(blocks):
            if b["t"] in ("choices", "choice_table", "passage"):
                break
            if b["t"] == "text":
                pts_idx = i

        first_text_done = False
        for i, b in enumerate(blocks):
            if b["t"] == "text":
                prefix = ""
                if not first_text_done:
                    prefix = f"{no}. "
                    first_text_done = True
                tail = ""
                if pts_idx == i and pts is not None and points_style == "tail":
                    p = int(pts) if float(pts).is_integer() else pts
                    tail = f" ({p}점)"
                if prefix:
                    self.hwp.set_font(Bold=True, Height=BODY_PT, FaceName=BODY_FONT)
                    self.text(prefix)
                    self.hwp.set_font(Bold=False, Height=BODY_PT, FaceName=BODY_FONT)
                self.text(b["text"] + tail)
                self.hwp.insert_text("\r\n")
            elif b["t"] == "image":
                if b.get("file"):
                    p = os.path.join(asset_dir, b["file"].replace("/", os.sep))
                    if os.path.exists(p):
                        self.image(p, b.get("width_pt"), b.get("height_pt"))
            elif b["t"] == "passage":
                self.passage_box(b["lines"])
            elif b["t"] == "choices":
                self.choices(b["items"])
            elif b["t"] == "choice_table":
                self.choice_table(b["headers"], b["rows"])
        self.para()  # 문항 간 여백

    # ---------- 저장/종료 ----------
    def save(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        return self.hwp.save_as(path)

    def save_pdf(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        return self.hwp.save_as(path, format="PDF")

    def quit(self):
        try:
            self.hwp.quit()
        except Exception:
            pass


def build_exam(exam, out_hwp, asset_dir, mode="copy", pdf_also=None):
    """exam.json → 시험지 .hwp (mode: copy=원문항, variant=변형문항)."""
    meta = exam["meta"]
    w = ExamWriter(visible=False)
    try:
        w.page_setup()
        w.base_font()
        kind = "기출 카피본" if mode == "copy" else "변형 문제"
        title = f"{meta['year']}학년도 {meta['school']} {meta['grade']}학년 {meta['term']}"
        w.title_block(
            f"{meta['subject']} — {kind}",
            title,
            "학년:        반:        이름:                    점수:        ",
        )
        w.two_columns()

        if mode == "copy":
            for q in exam["questions"]:
                w.question(q, asset_dir)
        else:
            n = 0
            for q in exam["questions"]:
                for v in q.get("variants") or []:
                    n += 1
                    if (v.get("layout") or {}).get("break_before") == "column":
                        w.column_break()
                    vq = {
                        "no": n,
                        "points": q.get("points"),
                        "blocks": v["blocks"],
                    }
                    w.question(vq, asset_dir)
        ok = w.save(out_hwp)
        if pdf_also:
            w.save_pdf(pdf_also)
        return ok
    finally:
        w.quit()
