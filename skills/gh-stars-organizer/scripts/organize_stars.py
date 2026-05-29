#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def default_output_dir() -> Path:
    date = datetime.now().date().isoformat()
    return Path("output") / "github-stars" / date


def run_step(args: list[str]) -> None:
    cmd = [sys.executable, str(SCRIPT_DIR / args[0]), *args[1:]]
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="一键整理 GitHub stars：拉取、分类、渲染、生成同步计划。")
    parser.add_argument("--output-dir", type=Path, default=default_output_dir())
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--apply-lists", action="store_true", help="实际写入 GitHub Lists。默认只生成计划。")
    parser.add_argument("--public-lists", action="store_true", help="新建 GitHub List 时设为公开。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw = args.output_dir / "stars_raw.json"
    classified = args.output_dir / "stars_classified.json"

    fetch_args = ["fetch_stars.py", "--output", str(raw)]
    if args.max_pages:
        fetch_args.extend(["--max-pages", str(args.max_pages)])
    run_step(fetch_args)
    run_step(["classify_stars.py", str(raw), "--output", str(classified)])
    run_step(["render_markdown.py", str(classified)])

    sync_args = ["sync_github_lists.py", str(classified)]
    sync_args.append("--apply" if args.apply_lists else "--dry-run")
    if args.public_lists:
        sync_args.append("--public-lists")
    run_step(sync_args)


if __name__ == "__main__":
    main()
