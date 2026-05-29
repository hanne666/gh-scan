#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path

from common import normalize_star_record, now_iso, write_json


def default_output() -> Path:
    date = datetime.now().date().isoformat()
    return Path("output") / "github-stars" / date / "stars_raw.json"


def run_gh_json(args: list[str]) -> list[dict]:
    proc = subprocess.run(args, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    import json

    data = json.loads(proc.stdout)
    if not isinstance(data, list):
        raise SystemExit("GitHub API response is not a list")
    return data


def fetch_stars(*, per_page: int, max_pages: int | None) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        if max_pages is not None and page > max_pages:
            break
        endpoint = f"/user/starred?per_page={per_page}&page={page}"
        page_items = run_gh_json([
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github.star+json",
            endpoint,
        ])
        if not page_items:
            break
        items.extend(normalize_star_record(item) for item in page_items)
        if len(page_items) < per_page:
            break
        page += 1
    return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="读取当前 GitHub 账号的 starred repositories。")
    parser.add_argument("--output", type=Path, default=default_output())
    parser.add_argument("--per-page", type=int, default=100)
    parser.add_argument("--max-pages", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    items = fetch_stars(per_page=args.per_page, max_pages=args.max_pages)
    write_json(args.output, {
        "generated_at": now_iso(),
        "count": len(items),
        "items": items,
    })
    print(f"saved {len(items)} starred repositories -> {args.output}")


if __name__ == "__main__":
    main()
