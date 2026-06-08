from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                source_type TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                published_at TEXT NOT NULL,
                language TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS structured_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id INTEGER NOT NULL UNIQUE,
                structured_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(news_id) REFERENCES news(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL,
                title TEXT NOT NULL,
                report_json TEXT NOT NULL,
                markdown TEXT NOT NULL,
                validation_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def insert_news_items(items: list[dict[str, Any]]) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    inserted = 0
    with get_connection() as conn:
        for item in items:
            try:
                conn.execute(
                    """
                    INSERT INTO news
                    (title, content, source, source_type, url, published_at, language, raw_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["title"],
                        item["content"],
                        item["source"],
                        item["source_type"],
                        item["url"],
                        item["published_at"],
                        item["language"],
                        json.dumps(item, ensure_ascii=False),
                        now,
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                continue
    return inserted


def list_news(limit: int = 50, published_date: str | None = None) -> list[dict[str, Any]]:
    where = ""
    params: list[Any] = []
    if published_date:
        where = "WHERE published_at = ?"
        params.append(published_date)
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM news {where} ORDER BY published_at DESC, id DESC LIMIT ?",
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def list_recent_news(limit: int = 20) -> list[dict[str, Any]]:
    return list_news(limit)


def list_news_by_date(report_date: str, limit: int = 20) -> list[dict[str, Any]]:
    return list_news(limit=limit, published_date=report_date)


def upsert_structured(news_id: int, structured: dict[str, Any]) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO structured_news (news_id, structured_json, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(news_id) DO UPDATE SET
                structured_json = excluded.structured_json,
                created_at = excluded.created_at
            """,
            (news_id, json.dumps(structured, ensure_ascii=False), now),
        )


def list_structured(limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT n.*, s.structured_json
            FROM news n
            JOIN structured_news s ON s.news_id = n.id
            ORDER BY n.published_at DESC, n.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    records = []
    for row in rows:
        item = dict(row)
        item["structured"] = json.loads(item.pop("structured_json"))
        records.append(item)
    return records


def insert_report(report_date: str, title: str, report: dict[str, Any], markdown: str, validation: dict[str, Any]) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO reports (report_date, title, report_json, markdown, validation_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                report_date,
                title,
                json.dumps(report, ensure_ascii=False),
                markdown,
                json.dumps(validation, ensure_ascii=False),
                now,
            ),
        )
        return int(cursor.lastrowid)


def list_reports(limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, report_date, title, created_at FROM reports ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_report(report_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    if not row:
        return None
    item = dict(row)
    item["report"] = json.loads(item.pop("report_json"))
    item["validation"] = json.loads(item.pop("validation_json"))
    return item


def export_report_files(report_id: int, markdown: str, report: dict[str, Any]) -> None:
    reports_dir = Path(DB_PATH).parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / f"report_{report_id}.md").write_text(markdown, encoding="utf-8")
    (reports_dir / f"report_{report_id}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
