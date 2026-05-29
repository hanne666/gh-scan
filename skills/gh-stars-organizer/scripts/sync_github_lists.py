#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from common import MANAGED_LISTS, extract_items, now_iso, read_json, target_list_for, write_json


def gh_graphql(query: str, fields: list[tuple[str, str]] | None = None) -> dict[str, Any]:
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in fields or []:
        cmd.extend(["-F", f"{key}={value}"])
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    return json.loads(proc.stdout)


def fetch_user_lists() -> dict[str, dict[str, Any]]:
    query = """
    query {
      viewer {
        lists(first: 100) {
          nodes { id name isPrivate description }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """
    data = gh_graphql(query)
    lists = data["data"]["viewer"]["lists"]
    if lists["pageInfo"]["hasNextPage"]:
        raise SystemExit("viewer has more than 100 lists; pagination support is required")
    return {item["name"]: item for item in lists["nodes"]}


def fetch_list_items(list_id: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    cursor: str | None = None
    while True:
        if cursor:
            item_args = "first: 100, after: $cursor"
            fields = [("listId", list_id), ("cursor", cursor)]
            query = f"""
            query($listId: ID!, $cursor: String) {{
              node(id: $listId) {{
                ... on UserList {{
                  items({item_args}) {{
                    nodes {{ ... on Repository {{ id nameWithOwner url }} }}
                    pageInfo {{ hasNextPage endCursor }}
                  }}
                }}
              }}
            }}
            """
        else:
            fields = [("listId", list_id)]
            query = """
            query($listId: ID!) {
              node(id: $listId) {
                ... on UserList {
                  items(first: 100) {
                    nodes { ... on Repository { id nameWithOwner url } }
                    pageInfo { hasNextPage endCursor }
                  }
                }
              }
            }
            """
        data = gh_graphql(query, fields)
        node = data["data"]["node"]
        if not node:
            break
        connection = node["items"]
        items.extend(item for item in connection["nodes"] if item)
        if not connection["pageInfo"]["hasNextPage"]:
            break
        cursor = connection["pageInfo"]["endCursor"]
    return items


def build_memberships(lists_by_name: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    memberships: dict[str, list[dict[str, str]]] = {}
    for list_info in lists_by_name.values():
        for item in fetch_list_items(list_info["id"]):
            memberships.setdefault(item["id"], []).append({
                "id": list_info["id"],
                "name": list_info["name"],
            })
    return memberships


def create_user_list(name: str, *, private: bool) -> dict[str, Any]:
    query = """
    mutation($name: String!, $description: String, $isPrivate: Boolean) {
      createUserList(input: {
        name: $name,
        description: $description,
        isPrivate: $isPrivate
      }) {
        list { id name isPrivate description }
      }
    }
    """
    description = "gh-scan 管理的 GitHub stars 分类"
    data = gh_graphql(query, [
        ("name", name),
        ("description", description),
        ("isPrivate", "true" if private else "false"),
    ])
    return data["data"]["createUserList"]["list"]


def update_item_lists(item_id: str, list_ids: list[str]) -> list[dict[str, str]]:
    query = """
    mutation($itemId: ID!, $listIds: [ID!]!) {
      updateUserListsForItem(input: {itemId: $itemId, listIds: $listIds}) {
        lists { id name }
      }
    }
    """
    fields = [("itemId", item_id)]
    fields.extend(("listIds[]", list_id) for list_id in list_ids)
    data = gh_graphql(query, fields)
    return data["data"]["updateUserListsForItem"]["lists"]


def build_plan(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan = []
    for item in items:
        target = item.get("target_list") or target_list_for(item)
        if target not in MANAGED_LISTS:
            target = "待复核 Review Later"
        plan.append({
            "repo": item.get("full_name"),
            "url": item.get("html_url"),
            "node_id": item.get("node_id"),
            "target_list": target,
            "retention_level": item.get("retention_level"),
            "cleanup_advice": item.get("cleanup_advice"),
        })
    return plan


def apply_plan(plan: list[dict[str, Any]], *, private_lists: bool) -> tuple[int, int]:
    lists_by_name = fetch_user_lists()
    memberships = build_memberships(lists_by_name)
    created = 0
    updated = 0

    for name in MANAGED_LISTS:
        if name not in lists_by_name:
            lists_by_name[name] = create_user_list(name, private=private_lists)
            created += 1

    managed_ids = {item["id"] for name, item in lists_by_name.items() if name in MANAGED_LISTS}
    for entry in plan:
        item_id = entry.get("node_id")
        if not item_id:
            print(f"skip {entry.get('repo')}: missing node_id")
            continue
        target_id = lists_by_name[entry["target_list"]]["id"]
        current = memberships.get(item_id, [])
        preserved = [item["id"] for item in current if item["id"] not in managed_ids]
        desired = sorted(set(preserved + [target_id]))
        current_ids = sorted(item["id"] for item in current)
        if desired == current_ids:
            continue
        update_item_lists(item_id, desired)
        updated += 1
        print(f"updated {entry.get('repo')} -> {entry['target_list']}")
    return created, updated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="同步分类结果到 GitHub Lists。默认只生成计划。")
    parser.add_argument("input", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="只生成同步计划，不写 GitHub。默认行为。")
    mode.add_argument("--apply", action="store_true", help="实际创建 Lists 并更新仓库 List 关系。")
    parser.add_argument("--plan-output", type=Path)
    parser.add_argument("--public-lists", action="store_true", help="新建 List 时设为公开；默认私有。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    items = extract_items(read_json(args.input))
    plan = build_plan(items)
    plan_output = args.plan_output or args.input.with_name("lists_sync_plan.json")
    write_json(plan_output, {
        "generated_at": now_iso(),
        "mode": "apply" if args.apply else "dry-run",
        "count": len(plan),
        "items": plan,
    })

    if not args.apply:
        print(f"dry-run: wrote sync plan for {len(plan)} repositories -> {plan_output}")
        return

    created, updated = apply_plan(plan, private_lists=not args.public_lists)
    print(f"created {created} lists; updated {updated} repositories")


if __name__ == "__main__":
    main()
