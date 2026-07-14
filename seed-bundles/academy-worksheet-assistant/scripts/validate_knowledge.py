# -*- coding: utf-8 -*-
"""사용자 교육과정 지식팩을 검증하고 승인 상태를 설정에 활성화한다."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.profile import PROFILE_PATH, load_catalog, load_profile, validate_catalog, validate_profile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--activate", action="store_true", help="검증 통과 지식팩을 profile에 ready로 반영")
    args = parser.parse_args()

    try:
        profile = load_profile()
        catalog = load_catalog()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    errors = validate_profile(profile) + validate_catalog(catalog, profile)
    if errors:
        print(f"knowledge_status=pending errors={len(errors)}")
        for error in errors:
            print(" -", error)
        raise SystemExit(1)

    print("knowledge_status=validated errors=0")
    if args.activate:
        profile["knowledge_status"] = "ready"
        with PROFILE_PATH.open("w", encoding="utf-8") as handle:
            json.dump(profile, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"activated: {PROFILE_PATH}")
    else:
        print("활성화하려면 사용자 승인 후 --activate를 추가하세요.")


if __name__ == "__main__":
    main()
