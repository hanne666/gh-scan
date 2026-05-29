#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
TARGETS = [
    Path.home() / ".claude" / "skills",
    Path.home() / ".codex" / "skills",
]


def iter_skill_dirs() -> list[Path]:
    return [
        skill_dir
        for skill_dir in sorted(SKILLS.iterdir())
        if (skill_dir / "SKILL.md").exists()
    ]


def sync_one(skill_dir: Path, target_root: Path, *, apply: bool) -> None:
    target = target_root / skill_dir.name
    action = "update" if target.exists() or target.is_symlink() else "create"
    if not apply:
        print(f"dry-run: would {action} {target}")
        return

    tmp_target = target_root / f".{skill_dir.name}.tmp"
    if tmp_target.exists() or tmp_target.is_symlink():
        if tmp_target.is_symlink() or tmp_target.is_file():
            tmp_target.unlink()
        else:
            shutil.rmtree(tmp_target)

    target_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill_dir, tmp_target)

    if target.exists() or target.is_symlink():
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)
    tmp_target.rename(target)
    print(f"synced {skill_dir.name} -> {target}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="同步 gh-scan 子 skill 到 Claude Code 和 Codex 的安装目录。"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示将要同步的目标，不修改安装目录。默认行为。",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="实际写入 ~/.claude/skills 和 ~/.codex/skills。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_changes = bool(args.apply)

    if not apply_changes:
        print("dry-run mode; pass --apply to write installed skill copies")

    for skill_dir in iter_skill_dirs():
        for target_root in TARGETS:
            sync_one(skill_dir, target_root, apply=apply_changes)


if __name__ == "__main__":
    main()
