from __future__ import annotations

import email.utils
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from html import unescape
from typing import Any

from backend.config import RSS_FEEDS


def strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_date(value: str) -> str:
    if not value:
        return datetime.now(timezone.utc).date().isoformat()
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        return parsed.date().isoformat()
    except Exception:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
        except Exception:
            return datetime.now(timezone.utc).date().isoformat()


def child_text(node: ET.Element, names: list[str]) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text.strip()
    for child in node:
        local = child.tag.split("}", 1)[-1]
        if local in names and child.text:
            return child.text.strip()
    return ""


def child_link(node: ET.Element) -> str:
    link = child_text(node, ["link"])
    if link:
        return link
    for child in node:
        if child.tag.split("}", 1)[-1] == "link":
            href = child.attrib.get("href")
            if href:
                return href
    return ""


def parse_filter_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def in_date_range(published_at: str, start_date: date | None, end_date: date | None) -> bool:
    try:
        current = datetime.strptime(published_at, "%Y-%m-%d").date()
    except ValueError:
        return True
    if start_date and current < start_date:
        return False
    if end_date and current > end_date:
        return False
    return True


def get_sources() -> list[dict[str, str]]:
    return [
        {
            "id": feed["id"],
            "name": feed["name"],
            "source_type": feed["source_type"],
            "language": feed["language"],
            "url": feed["url"],
        }
        for feed in RSS_FEEDS
    ]


def select_feeds(source_ids: list[str] | None) -> list[dict[str, str]]:
    if not source_ids:
        return RSS_FEEDS
    allowed = set(source_ids)
    return [feed for feed in RSS_FEEDS if feed["id"] in allowed]


def parse_feed(
    xml_text: str,
    feed: dict[str, str],
    max_items: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    candidates = list(root.findall(".//item")) or list(root.findall(".//{http://www.w3.org/2005/Atom}entry"))
    items = []
    for node in candidates[:max_items]:
        title = strip_html(child_text(node, ["title"]))
        content = strip_html(
            child_text(node, ["description", "summary", "content", "{http://purl.org/rss/1.0/modules/content/}encoded"])
        )
        url = child_link(node)
        published_at = parse_date(child_text(node, ["pubDate", "published", "updated"]))
        if not title or not url:
            continue
        if not in_date_range(published_at, start_date, end_date):
            continue
        items.append(
            {
                "title": title,
                "content": content[:3000] or title,
                "source": feed["name"],
                "source_type": feed["source_type"],
                "url": url,
                "published_at": published_at,
                "language": feed["language"],
            }
        )
    return items


def fetch_rss(
    max_items_per_feed: int = 8,
    source_ids: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    all_items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    start = parse_filter_date(start_date)
    end = parse_filter_date(end_date)
    for feed in select_feeds(source_ids):
        request = urllib.request.Request(feed["url"], headers={"User-Agent": "DailyAIInsightEngine/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                xml_text = response.read().decode("utf-8", errors="replace")
            all_items.extend(parse_feed(xml_text, feed, max_items_per_feed, start, end))
        except Exception as exc:
            errors.append({"source": feed["name"], "error": str(exc)})
    return all_items, errors
