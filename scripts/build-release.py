# -*- coding: utf-8 -*-
"""시드 번들을 배포용 zip으로 묶는다.

사용법:
    python scripts/build-release.py

결과: dist/<slug>.zip (번들별 1개)

- .env, __pycache__, *.pyc는 제외한다 (실키/캐시가 배포물에 섞이지 않도록).
- zip 내부 최상위 폴더는 번들 slug로 고정되어, 풀면 바로 폴더가 생긴다.

릴리스 발행 예시:
    gh release create v0.1.0 dist/*.zip --title "v0.1.0" --notes "..."
"""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLES_DIR = ROOT / "seed-bundles"
DIST_DIR = ROOT / "dist"

EXCLUDE_NAMES = {".env", "__pycache__"}
EXCLUDE_SUFFIXES = {".pyc"}


def should_skip(path):
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return any(part in EXCLUDE_NAMES for part in path.parts)


def build_zip(bundle_dir):
    zip_path = DIST_DIR / f"{bundle_dir.name}.zip"
    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(bundle_dir.rglob("*")):
            if not file.is_file() or should_skip(file.relative_to(bundle_dir)):
                continue
            arcname = f"{bundle_dir.name}/{file.relative_to(bundle_dir).as_posix()}"
            zf.write(file, arcname)
            count += 1
    size_kb = zip_path.stat().st_size / 1024
    print(f"[OK] {zip_path.name}: {count} files, {size_kb:.1f} KB")
    return zip_path


def main():
    if not BUNDLES_DIR.is_dir():
        print(f"seed-bundles 폴더를 찾을 수 없습니다: {BUNDLES_DIR}", file=sys.stderr)
        return 1
    DIST_DIR.mkdir(exist_ok=True)
    bundles = [d for d in sorted(BUNDLES_DIR.iterdir()) if d.is_dir()]
    if not bundles:
        print("묶을 번들이 없습니다.", file=sys.stderr)
        return 1
    for bundle_dir in bundles:
        build_zip(bundle_dir)
    print(f"\n완료: {len(bundles)}개 번들 → {DIST_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
