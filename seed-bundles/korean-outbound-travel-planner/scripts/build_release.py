from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path


BUNDLE_ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = ["README.md", "bundle.json", ".env.example", "LICENSE"]
TREE_ROOTS = ["app/config", "app/tests", "app/travel_planner", "worker", "examples", "docs", "scripts"]
APP_FILES = ["app/README.md", "app/requirements.txt", "app/pytest.ini"]
BLOCKED_PARTS = {".env", ".venv", ".pytest_cache", "__pycache__", "data", "dist"}
BLOCKED_SUFFIXES = {".db", ".log", ".pyc", ".pyo"}
KEY_ASSIGNMENT = re.compile(
    r"(?i)(OPENAI_API_KEY|AMADEUS_CLIENT_SECRET|GOOGLE_MAPS_API_KEY|BOOKING_API_KEY|SKYSCANNER_API_KEY)[ \t]*=[ \t]*(?P<value>[^,\s#)]+)"
)
SECRET_TOKEN_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"),
]


def allowed(path: Path) -> bool:
    relative = path.relative_to(BUNDLE_ROOT)
    return not any(part in BLOCKED_PARTS for part in relative.parts) and path.suffix.lower() not in BLOCKED_SUFFIXES


def release_files() -> list[Path]:
    files = [BUNDLE_ROOT / name for name in [*ROOT_FILES, *APP_FILES]]
    for tree in TREE_ROOTS:
        root = BUNDLE_ROOT / tree
        files.extend(path for path in root.rglob("*") if path.is_file() and allowed(path))
    missing = [str(path.relative_to(BUNDLE_ROOT)) for path in files if not path.exists()]
    if missing:
        raise RuntimeError("필수 배포 파일이 없습니다: " + ", ".join(missing))
    unique = {path.resolve(): path for path in files if allowed(path)}
    return sorted(unique.values(), key=lambda path: str(path.relative_to(BUNDLE_ROOT)))


def validate(files: list[Path]) -> None:
    forbidden = [path for path in files if not allowed(path)]
    if forbidden:
        raise RuntimeError("배포 금지 파일 포함: " + ", ".join(str(path) for path in forbidden))
    for path in files:
        if path.name == ".env" or path.stat().st_size > 10 * 1024 * 1024:
            raise RuntimeError(f"민감하거나 비정상적으로 큰 파일: {path}")
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        assignment = KEY_ASSIGNMENT.search(content)
        assigned_value = assignment.group("value").strip("\"'").lower() if assignment else ""
        safe_fixture = not assigned_value or assigned_value.startswith(("test", "fake", "dummy", "fixture", "example"))
        if (assignment and not safe_fixture) or any(pattern.search(content) for pattern in SECRET_TOKEN_PATTERNS):
            raise RuntimeError(f"API 키로 보이는 값이 포함된 파일: {path.relative_to(BUNDLE_ROOT)}")


def build(output_dir: Path) -> Path:
    files = release_files()
    validate(files)
    output_dir = output_dir.resolve()
    if BUNDLE_ROOT.resolve() == output_dir or BUNDLE_ROOT.resolve() in output_dir.parents and output_dir.name != "dist":
        raise RuntimeError("배포 출력 경로는 번들 루트가 아닌 전용 dist 경로여야 합니다.")
    package_dir = output_dir / BUNDLE_ROOT.name
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    for source in files:
        destination = package_dir / source.relative_to(BUNDLE_ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    archive = output_dir / f"{BUNDLE_ROOT.name}.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle_zip:
        for path in package_dir.rglob("*"):
            if path.is_file():
                bundle_zip.write(path, path.relative_to(output_dir))
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a clean, allowlisted worker bundle archive.")
    parser.add_argument("--check-only", action="store_true", help="Validate the release allowlist without writing files.")
    parser.add_argument("--output", type=Path, default=BUNDLE_ROOT / "dist")
    args = parser.parse_args()
    files = release_files()
    validate(files)
    if args.check_only:
        print(f"release check passed: {len(files)} files")
        return 0
    archive = build(args.output)
    print(archive)
    return 0


if __name__ == "__main__":
    sys.exit(main())
