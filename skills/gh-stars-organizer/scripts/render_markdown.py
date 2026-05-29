#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from common import MANAGED_LISTS, extract_items, read_json, short_intro


def escape_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def render_inventory(items: list[dict]) -> str:
    lines = [
        "# GitHub 收藏仓库分类清单",
        "",
        f"- 仓库数量：{len(items)}",
        "- 说明：清理建议只作为待确认动作，不自动取消 star。",
        "",
    ]

    by_category: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_category[item.get("target_list") or item.get("category")].append(item)

    for category in MANAGED_LISTS:
        repos = sorted(
            by_category.get(category, []),
            key=lambda item: (item.get("retention_level", "P9"), -(item.get("stars") or 0)),
        )
        if not repos:
            continue
        lines.extend([
            f"## {category}",
            "",
            "| 项目 | stars | 简介 | 保留级别 | 清理建议 |",
            "|---|---:|---|---|---|",
        ])
        for repo in repos:
            name = escape_cell(repo.get("full_name") or repo.get("name"))
            url = repo.get("html_url") or "#"
            lines.append(
                "| "
                f"[{name}]({url}) | "
                f"{int(repo.get('stars') or 0)} | "
                f"{escape_cell(short_intro(repo))} | "
                f"{escape_cell(repo.get('retention_level'))} | "
                f"{escape_cell(repo.get('cleanup_advice'))} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_summary(items: list[dict]) -> str:
    categories = Counter(item.get("target_list") for item in items)
    levels = Counter(item.get("retention_level") for item in items)
    lines = [
        "# GitHub Lists 整理摘要",
        "",
        f"- 仓库数量：{len(items)}",
        f"- 待复核数量：{categories.get('待复核 Review Later', 0)}",
        "",
        "## 分类统计",
        "",
        "| 分类 | 数量 |",
        "|---|---:|",
    ]
    for category in MANAGED_LISTS:
        lines.append(f"| {category} | {categories.get(category, 0)} |")
    lines.extend([
        "",
        "## 保留级别统计",
        "",
        "| 保留级别 | 数量 |",
        "|---|---:|",
    ])
    for level in ["P0", "P1", "P2", "P3"]:
        lines.append(f"| {level} | {levels.get(level, 0)} |")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="把分类结果渲染为 Markdown 清单。")
    parser.add_argument("input", type=Path)
    parser.add_argument("--inventory-output", type=Path)
    parser.add_argument("--summary-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    items = extract_items(read_json(args.input))
    inventory = args.inventory_output or args.input.with_name("github_stars_inventory.md")
    summary = args.summary_output or args.input.with_name("lists_summary.md")
    inventory.write_text(render_inventory(items), encoding="utf-8")
    summary.write_text(render_summary(items), encoding="utf-8")
    print(f"rendered inventory -> {inventory}")
    print(f"rendered summary -> {summary}")


if __name__ == "__main__":
    main()
