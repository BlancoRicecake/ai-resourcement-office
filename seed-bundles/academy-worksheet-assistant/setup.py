# -*- coding: utf-8 -*-
"""학원 문제지 조교 최초 설정 마법사."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "config" / "profile.json"


def ask(label, current=None, required=True):
    suffix = f" [{current}]" if current else ""
    while True:
        value = input(f"{label}{suffix}: ").strip() or (str(current) if current else "")
        if value or not required:
            return value
        print("필수 항목입니다.")


def build_profile(values):
    formats = [item.strip().lower() for item in values["output_formats"].split(",") if item.strip()]
    unsupported = sorted(set(formats) - {"hwp", "pdf"})
    if unsupported:
        raise ValueError(f"현재 지원하지 않는 출력 형식: {', '.join(unsupported)}")
    return {
        "schema_version": "1.0",
        "worker": "학원 문제지 조교",
        "setup_status": "complete",
        "knowledge_status": "pending",
        "subject": values["subject"],
        "school_level": values["school_level"],
        "grade": values["grade"],
        "exam_year": str(values["exam_year"]),
        "curriculum": values["curriculum"],
        "curriculum_source": values.get("curriculum_source") or None,
        "default_school": values.get("default_school") or None,
        "publisher": values.get("publisher") or None,
        "textbook_title": values.get("textbook_title") or None,
        "input_format": "pdf",
        "output_formats": formats,
        "layout_notes": values.get("layout_notes") or None,
    }


def markdown_files(profile):
    return {
        ROOT / "memory" / "USER.md": (
            "# USER\n\n"
            f"- 주 사용 과목: {profile['subject']}\n"
            f"- 기본 출력 형식: {', '.join(profile['output_formats'])}\n"
            f"- 편집·레이아웃 선호: {profile.get('layout_notes') or '미정'}\n\n"
            "사용자가 승인한 선호만 이 파일에 누적한다. 개인정보는 기록하지 않는다.\n"
        ),
        ROOT / "memory" / "PROJECT.md": (
            "# PROJECT\n\n"
            f"- 학교급: {profile['school_level']}\n"
            f"- 기본 학년: {profile['grade']}\n"
            f"- 기준 시험 연도: {profile['exam_year']}\n"
            f"- 과목: {profile['subject']}\n"
            f"- 교육과정: {profile['curriculum']}\n"
            f"- 교육과정 출처: {profile.get('curriculum_source') or '미등록'}\n"
            f"- 출판사/교재: {profile.get('publisher') or '미정'} / {profile.get('textbook_title') or '미정'}\n"
            f"- 지식 준비 상태: {profile['knowledge_status']}\n"
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="학원 문제지 조교 최초 설정")
    parser.add_argument("--subject")
    parser.add_argument("--school-level")
    parser.add_argument("--grade")
    parser.add_argument("--exam-year")
    parser.add_argument("--curriculum")
    parser.add_argument("--curriculum-source")
    parser.add_argument("--default-school")
    parser.add_argument("--publisher")
    parser.add_argument("--textbook-title")
    parser.add_argument("--output-formats", default="hwp,pdf")
    parser.add_argument("--layout-notes")
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preview-file", help="dry-run JSON을 저장할 경로")
    return parser.parse_args()


def main():
    args = parse_args()
    values = vars(args)
    if not args.non_interactive:
        print("학원 문제지 조교 최초 설정을 시작합니다. 과목 지식은 이 단계에서 임의 생성하지 않습니다.\n")
        values["subject"] = ask("사용할 과목", args.subject)
        values["school_level"] = ask("학교급", args.school_level or "중학교")
        values["grade"] = ask("기본 학년", args.grade)
        values["exam_year"] = ask("기준 시험 연도", args.exam_year)
        values["curriculum"] = ask("적용 교육과정 이름", args.curriculum)
        values["curriculum_source"] = ask("공식 교육과정 파일 경로 또는 URL", args.curriculum_source, required=False)
        values["default_school"] = ask("기본 학교/학원명", args.default_school, required=False)
        values["publisher"] = ask("교과서 출판사", args.publisher, required=False)
        values["textbook_title"] = ask("교재명", args.textbook_title, required=False)
        values["output_formats"] = ask("출력 형식(hwp,pdf 중 쉼표 구분)", args.output_formats)
        values["layout_notes"] = ask("레이아웃 선호", args.layout_notes, required=False)
    else:
        missing = [key for key in ("subject", "school_level", "grade", "exam_year", "curriculum") if not values.get(key)]
        if missing:
            raise SystemExit(f"비대화식 설정 필수 인자 누락: {', '.join(missing)}")

    try:
        profile = build_profile(values)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    rendered = json.dumps(profile, ensure_ascii=False, indent=2) + "\n"
    if args.dry_run:
        if args.preview_file:
            target = Path(args.preview_file)
            if not target.is_absolute():
                target = ROOT / target
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rendered, encoding="utf-8")
            print(f"preview: {target}")
        print(rendered, end="")
        return

    if PROFILE_PATH.exists() and not args.force:
        raise SystemExit("기존 설정이 있습니다. 덮어쓰려면 --force를 사용하세요.")
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(rendered, encoding="utf-8")
    for path, content in markdown_files(profile).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if args.force or not path.exists():
            path.write_text(content, encoding="utf-8")
    print(f"설정 저장: {PROFILE_PATH}")
    print("다음 단계: 교육과정 자료를 knowledge/curriculum.json으로 구조화하고 사용자가 승인해야 변형문제 제작이 활성화됩니다.")


if __name__ == "__main__":
    main()
