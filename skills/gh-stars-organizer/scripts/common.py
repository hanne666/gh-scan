#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRESET_LISTS = [
    "AI 编程与 Agent IDE",
    "Agent 框架与多 Agent",
    "MCP 与 Skills",
    "RAG 与文档处理",
    "Prompt 与 LLM 工具",
    "自动化与爬虫",
    "UI 与应用模板",
    "开发基础设施与 CLI",
    "内容与媒体 AI",
    "待复核 Review Later",
]
REVIEW_LATER = "待复核 Review Later"
GH_SCAN_LIST_DESCRIPTION = "gh-scan 管理的 GitHub stars 分类"
MAX_GITHUB_LISTS = 8
GENERIC_TOPICS = {
    "awesome", "app", "apps", "tool", "tools", "demo", "example", "examples",
    "library", "framework", "template", "starter", "boilerplate", "plugin",
    "plugins", "extension", "extensions", "open-source", "opensource",
}
TOPIC_DISPLAY_OVERRIDES = {
    "ai": "AI",
    "api": "API",
    "cli": "CLI",
    "llm": "LLM",
    "mcp": "MCP",
    "ocr": "OCR",
    "pdf": "PDF",
    "rag": "RAG",
    "sdk": "SDK",
    "ui": "UI",
}

CATEGORY_KEYWORDS = {
    "AI 编程与 Agent IDE": [
        "claude code", "codex", "cursor", "aider", "opencode", "openclaw",
        "windsurf", "ai ide", "coding agent", "code agent", "vscode",
    ],
    "Agent 框架与多 Agent": [
        "agent", "multi-agent", "multi agent", "crewai", "autogen",
        "langgraph", "swarm", "orchestration", "sandbox", "daytona",
    ],
    "MCP 与 Skills": [
        "mcp", "model context protocol", "skill", "skills", "claude skill",
        "server", "tool calling",
    ],
    "RAG 与文档处理": [
        "rag", "ocr", "pdf", "document", "markdown", "embedding", "vector",
        "knowledge", "mineru", "retrieval", "notebook",
    ],
    "Prompt 与 LLM 工具": [
        "prompt", "prompts", "llm", "chatgpt", "system prompt", "eval",
        "token", "tokenizer", "inference",
    ],
    "自动化与爬虫": [
        "automation", "automate", "crawler", "scrape", "scraper", "spider",
        "playwright", "puppeteer", "browser", "bot", "downloader",
    ],
    "UI 与应用模板": [
        "ui", "template", "starter", "nextjs", "react", "vue", "svelte",
        "tauri", "electron", "dashboard", "shadcn", "frontend",
    ],
    "开发基础设施与 CLI": [
        "cli", "terminal", "devops", "docker", "kubernetes", "database",
        "api", "framework", "rust", "golang", "python", "package",
    ],
    "内容与媒体 AI": [
        "image", "video", "audio", "tts", "asr", "whisper", "diffusion",
        "stable diffusion", "media", "content", "youtube", "subtitle",
    ],
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    raise SystemExit("input must be a JSON list or an object with items[]")


def normalize_star_record(record: dict[str, Any]) -> dict[str, Any]:
    repo = record.get("repo") or record.get("repository") or record
    owner = repo.get("owner") or {}
    license_info = repo.get("license") or {}
    topics = repo.get("topics") or []
    if not isinstance(topics, list):
        topics = []

    return {
        "starred_at": record.get("starred_at"),
        "id": repo.get("id"),
        "node_id": repo.get("node_id"),
        "name": repo.get("name") or "",
        "full_name": repo.get("full_name") or "",
        "owner": owner.get("login") if isinstance(owner, dict) else "",
        "html_url": repo.get("html_url") or "",
        "description": repo.get("description") or "",
        "language": repo.get("language") or "",
        "topics": topics,
        "stars": repo.get("stargazers_count") or repo.get("stars") or 0,
        "forks": repo.get("forks_count") or 0,
        "fork": bool(repo.get("fork")),
        "archived": bool(repo.get("archived")),
        "disabled": bool(repo.get("disabled")),
        "pushed_at": repo.get("pushed_at"),
        "updated_at": repo.get("updated_at"),
        "license": license_info.get("spdx_id") if isinstance(license_info, dict) else None,
    }


def repo_text(repo: dict[str, Any]) -> str:
    parts = [
        repo.get("full_name", ""),
        repo.get("name", ""),
        repo.get("description", ""),
        repo.get("language", ""),
        " ".join(repo.get("topics") or []),
    ]
    return " ".join(str(part).lower() for part in parts if part)


def normalize_topic(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9.+#-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    if len(text) < 2 or text in GENERIC_TOPICS:
        return ""
    return text


def display_topic(value: str) -> str:
    if value in TOPIC_DISPLAY_OVERRIDES:
        return TOPIC_DISPLAY_OVERRIDES[value]
    parts = value.replace("-", " ").split()
    return " ".join(TOPIC_DISPLAY_OVERRIDES.get(part, part) for part in parts)


def topic_list(repo: dict[str, Any]) -> list[str]:
    topics = repo.get("topics") or []
    if not isinstance(topics, list):
        return []
    normalized = [normalize_topic(topic) for topic in topics]
    return [topic for topic in normalized if topic]


def infer_dynamic_taxonomy(
    repos: list[dict[str, Any]],
    *,
    max_categories: int = MAX_GITHUB_LISTS,
    min_category_size: int = 2,
) -> dict[str, Any]:
    topic_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()
    for repo in repos:
        topic_counts.update(topic_list(repo))
        language = str(repo.get("language") or "").strip()
        if language:
            language_counts[language] += 1

    selected_topics = [
        topic
        for topic, count in topic_counts.most_common()
        if count >= min_category_size
    ][:max_categories]
    if not selected_topics and topic_counts:
        selected_topics = [topic for topic, _ in topic_counts.most_common(max_categories)]

    selected_languages = [
        language
        for language, _ in language_counts.most_common()
        if language
    ][: max(0, max_categories - len(selected_topics))]

    return {
        "topic_rank": {topic: index for index, topic in enumerate(selected_topics)},
        "language_rank": {language: index for index, language in enumerate(selected_languages)},
    }


def classify_dynamic_category(
    repo: dict[str, Any],
    taxonomy: dict[str, Any],
) -> tuple[str, int, list[str]]:
    topic_rank = taxonomy.get("topic_rank") or {}
    language_rank = taxonomy.get("language_rank") or {}
    ranked_topics = [
        topic
        for topic in topic_list(repo)
        if topic in topic_rank
    ]
    if ranked_topics:
        topic = sorted(ranked_topics, key=lambda item: topic_rank[item])[0]
        return f"主题：{display_topic(topic)}", 2, [topic]

    language = str(repo.get("language") or "").strip()
    if language and language in language_rank:
        return f"语言：{language}", 1, [language]

    return REVIEW_LATER, 0, []


def classify_preset_category(repo: dict[str, Any]) -> tuple[str, int, list[str]]:
    text = repo_text(repo)
    scores: list[tuple[int, int, str, list[str]]] = []
    for priority, (category, keywords) in enumerate(CATEGORY_KEYWORDS.items()):
        matched = [keyword for keyword in keywords if keyword in text]
        if matched:
            scores.append((len(matched), -priority, category, matched))
    if not scores:
        return REVIEW_LATER, 0, []
    scores.sort(reverse=True)
    score, _, category, matched = scores[0]
    return category, score, matched


def classify_category(
    repo: dict[str, Any],
    *,
    category_mode: str = "dynamic",
    taxonomy: dict[str, Any] | None = None,
) -> tuple[str, int, list[str]]:
    if category_mode == "preset":
        return classify_preset_category(repo)
    if taxonomy is None:
        taxonomy = infer_dynamic_taxonomy([repo])
    return classify_dynamic_category(repo, taxonomy)


def freshness_score(repo: dict[str, Any], *, now: datetime | None = None) -> tuple[int, str]:
    if repo.get("archived") or repo.get("disabled"):
        return 0, "archived / disabled"
    now = now or datetime.now(timezone.utc)
    dt = parse_time(repo.get("pushed_at")) or parse_time(repo.get("updated_at"))
    if dt is None:
        return 20, "无更新时间"
    days = max((now - dt).days, 0)
    if days <= 30:
        return 100, "30 天内更新"
    if days <= 90:
        return 90, "90 天内更新"
    if days <= 180:
        return 75, "180 天内更新"
    if days <= 365:
        return 55, "半年未更新"
    if days <= 365 * 3:
        return 30, "一年未更新"
    return 10, "三年未更新"


def retention_for(
    repo: dict[str, Any],
    *,
    category_confidence: int,
    duplicate_name: bool,
    now: datetime | None = None,
) -> tuple[str, str]:
    stars = int(repo.get("stars") or 0)
    score, label = freshness_score(repo, now=now)

    if repo.get("archived") or repo.get("disabled"):
        return "P3", "仓库已归档或禁用，放入待复核，不自动取消收藏"
    if duplicate_name:
        return "P2", "同名项目重复，建议人工确认是否保留"
    if repo.get("fork"):
        return "P2", "fork 项目，建议确认是否已有主线项目"
    if score <= 10:
        if stars >= 5000:
            return "P2", "超过 3 年未更新但 star 较高，建议人工复核"
        return "P3", "超过 3 年未更新，列为清理候选"
    if score <= 30:
        if stars >= 5000:
            return "P1", "一年以上未更新但社区验证较强，可暂时保留"
        return "P2", "一年以上未更新，放入待复核"
    if category_confidence == 0:
        return "P2", "用途或分类不明确，放入待复核"
    if stars >= 5000 and score >= 75 and category_confidence >= 2:
        return "P0", "高 star 且近期活跃，核心保留"
    if stars < 100 and score < 75:
        return "P2", "低 star 且维护活跃度一般，建议复核"
    return "P1", f"{label}，用途较明确，普通保留"


def target_list_for(item: dict[str, Any]) -> str:
    if item.get("retention_level") in {"P2", "P3"}:
        return REVIEW_LATER
    category = item.get("category") or REVIEW_LATER
    return category


def category_order(items: list[dict[str, Any]]) -> list[str]:
    counts = Counter(item.get("target_list") or item.get("category") or REVIEW_LATER for item in items)
    categories = [
        category
        for category, _ in counts.most_common()
        if category and category != REVIEW_LATER
    ]
    if counts.get(REVIEW_LATER):
        categories.append(REVIEW_LATER)
    return categories


def enforce_list_limit(
    items: list[dict[str, Any]],
    *,
    max_lists: int = MAX_GITHUB_LISTS,
) -> list[dict[str, Any]]:
    max_lists = max(2, max_lists)
    counts = Counter(item.get("target_list") or REVIEW_LATER for item in items)
    if len(counts) <= max_lists:
        return items

    non_review = [
        (name, count)
        for name, count in counts.items()
        if name != REVIEW_LATER
    ]
    non_review.sort(key=lambda item: (-item[1], item[0]))
    keep_count = max_lists - 1
    kept = {name for name, _ in non_review[:keep_count]}

    for item in items:
        target = item.get("target_list") or REVIEW_LATER
        if target == REVIEW_LATER or target in kept:
            continue
        item["original_target_list"] = target
        item["target_list"] = REVIEW_LATER
        item["list_limit_note"] = f"GitHub Lists 分类上限为 {max_lists} 类，低频分类并入待复核"
    return items


def short_intro(repo: dict[str, Any], *, max_chars: int = 150) -> str:
    description = (repo.get("description") or "").strip()
    if not description:
        description = "暂无明确简介，需结合 README 或源码进一步确认。"
    if len(description) <= max_chars:
        return description
    return description[: max_chars - 1].rstrip() + "…"
