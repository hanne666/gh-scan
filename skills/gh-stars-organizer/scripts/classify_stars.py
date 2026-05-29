#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from common import (
    classify_category,
    extract_items,
    freshness_score,
    normalize_star_record,
    now_iso,
    read_json,
    retention_for,
    target_list_for,
    write_json,
)


def default_output(input_path: Path) -> Path:
    return input_path.with_name("stars_classified.json")


def parse_today(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def classify_items(raw_items: list[dict], *, now: datetime | None = None) -> list[dict]:
    repos = [normalize_star_record(item) for item in raw_items]
    name_counts = Counter((repo.get("name") or "").lower() for repo in repos)
    classified: list[dict] = []

    for repo in repos:
        category, confidence, matched = classify_category(repo)
        duplicate_name = name_counts[(repo.get("name") or "").lower()] > 1
        retention, advice = retention_for(
            repo,
            category_confidence=confidence,
            duplicate_name=duplicate_name,
            now=now,
        )
        score, freshness_label = freshness_score(repo, now=now)
        item = {
            **repo,
            "category": category,
            "category_confidence": confidence,
            "matched_keywords": matched,
            "freshness_score": score,
            "freshness_label": freshness_label,
            "duplicate_name": duplicate_name,
            "retention_level": retention,
            "cleanup_advice": advice,
        }
        item["target_list"] = target_list_for(item)
        classified.append(item)
    return classified


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按 gh-scan 规则自动分类 GitHub stars。")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--today", help="用于测试的日期，例如 2026-05-29。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    now = parse_today(args.today)
    raw_payload = read_json(args.input)
    items = classify_items(extract_items(raw_payload), now=now)
    output = args.output or default_output(args.input)
    write_json(output, {
        "generated_at": now_iso(),
        "source": str(args.input),
        "count": len(items),
        "items": items,
    })
    print(f"classified {len(items)} repositories -> {output}")


if __name__ == "__main__":
    main()
