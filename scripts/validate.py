#!/usr/bin/env python3
from __future__ import annotations

import argparse
import filecmp
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
SKILL_NAMES = ["gh-repo-scan", "gh-stars-organizer"]
INSTALL_ROOTS = [
    Path.home() / ".claude" / "skills",
    Path.home() / ".codex" / "skills",
]
REQUIRED = [
    ROOT / "skills" / "gh-repo-scan" / "SKILL.md",
    ROOT / "skills" / "gh-repo-scan" / "agents" / "openai.yaml",
    ROOT / "skills" / "gh-repo-scan" / "references" / "criteria.md",
    ROOT / "skills" / "gh-stars-organizer" / "SKILL.md",
    ROOT / "skills" / "gh-stars-organizer" / "agents" / "openai.yaml",
    ROOT / "skills" / "gh-stars-organizer" / "references" / "categories.md",
    ROOT / "skills" / "gh-stars-organizer" / "references" / "freshness.md",
    ROOT / "skills" / "gh-stars-organizer" / "references" / "repo-scan-criteria.md",
    ROOT / "skills" / "gh-stars-organizer" / "scripts" / "common.py",
    ROOT / "skills" / "gh-stars-organizer" / "scripts" / "fetch_stars.py",
    ROOT / "skills" / "gh-stars-organizer" / "scripts" / "classify_stars.py",
    ROOT / "skills" / "gh-stars-organizer" / "scripts" / "render_markdown.py",
    ROOT / "skills" / "gh-stars-organizer" / "scripts" / "sync_github_lists.py",
    ROOT / "skills" / "gh-stars-organizer" / "scripts" / "organize_stars.py",
    ROOT / "shared" / "repo-scan-criteria.md",
    ROOT / "shared" / "freshness.md",
    ROOT / "shared" / "categories.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证 gh-scan 套件结构和安装副本状态。")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="把安装副本未同步、空脚本目录等警告也视为失败。",
    )
    return parser.parse_args()


def validate_skill(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SystemExit(f"{path}: missing frontmatter")
    frontmatter = text.split("---", 2)[1]
    if "name:" not in frontmatter or "description:" not in frontmatter:
        raise SystemExit(f"{path}: missing name or description")
    if len(text.splitlines()) > 220:
        raise SystemExit(f"{path}: too long")


def validate_openai_yaml(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    required_fields = ["interface:", "display_name:", "short_description:", "default_prompt:"]
    missing = [field for field in required_fields if field not in text]
    if missing:
        raise SystemExit(f"{path}: missing {', '.join(missing)}")


def dircmp_has_diff(left: Path, right: Path) -> bool:
    cmp = filecmp.dircmp(left, right)
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return True
    return any(
        dircmp_has_diff(left / name, right / name)
        for name in cmp.common_dirs
    )


def collect_warnings() -> list[str]:
    warnings: list[str] = []

    for scripts_dir in SKILLS.glob("*/scripts"):
        if scripts_dir.is_dir() and not any(scripts_dir.iterdir()):
            warnings.append(f"empty scripts directory: {scripts_dir}")

    for skill_name in SKILL_NAMES:
        source = SKILLS / skill_name
        for install_root in INSTALL_ROOTS:
            installed = install_root / skill_name
            if not installed.exists():
                warnings.append(f"installed copy missing: {installed}")
            elif dircmp_has_diff(source, installed):
                warnings.append(f"installed copy out of sync: {installed}")

    return warnings


def main() -> None:
    args = parse_args()
    for path in REQUIRED:
        if not path.exists():
            raise SystemExit(f"missing {path}")
        if path.name == "SKILL.md":
            validate_skill(path)
        if path.name == "openai.yaml":
            validate_openai_yaml(path)

    warnings = collect_warnings()
    for warning in warnings:
        print(f"warning: {warning}")

    if args.strict and warnings:
        raise SystemExit("gh-scan suite has warnings")

    print("gh-scan suite valid")


if __name__ == "__main__":
    main()
