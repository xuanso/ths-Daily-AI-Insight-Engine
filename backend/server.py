from __future__ import annotations

import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend.agents.data_filter_agent import DataFilterAgent
from backend.agents.orchestrator import generate_daily_report
from backend.config import FRONTEND_DIR
from backend.services import database
from backend.services.crawler import fetch_rss, get_sources
from backend.services.deepseek_client import DeepSeekClient


def json_bytes(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def filter_news_items(items: list[dict]) -> tuple[list[dict], list[dict]]:
    client = DeepSeekClient()
    if not client.available:
        raise RuntimeError("DEEPSEEK_API_KEY is required to filter crawled news")
    agent = DataFilterAgent(client)
    passed = []
    results = []
    for item in items:
        decision = agent.run(item)
        results.append(
            {
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "url": item.get("url", ""),
                **decision,
            }
        )
        if decision["is_ai_opinion_news"]:
            enriched = dict(item)
            enriched["filter_json"] = decision
            passed.append(enriched)
    return passed, results


class Handler(BaseHTTPRequestHandler):
    server_version = "DailyAIInsightEngine/1.0"

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/health":
                return self.send_json({"ok": True})
            if parsed.path == "/api/sources":
                return self.send_json({"items": get_sources()})
            if parsed.path == "/api/news":
                params = parse_qs(parsed.query)
                limit = int(params.get("limit", ["50"])[0])
                published_date = params.get("date", [None])[0]
                return self.send_json({"items": database.list_news(limit, published_date)})
            if parsed.path == "/api/structured":
                params = parse_qs(parsed.query)
                limit = int(params.get("limit", ["20"])[0])
                return self.send_json({"items": database.list_structured(limit)})
            if parsed.path == "/api/reports":
                return self.send_json({"items": database.list_reports()})
            if parsed.path.startswith("/api/reports/"):
                report_id = int(parsed.path.rsplit("/", 1)[-1])
                report = database.get_report(report_id)
                if not report:
                    return self.send_json({"error": "report not found"}, status=404)
                return self.send_json(report)
            return self.serve_static(parsed.path)
        except Exception as exc:
            return self.send_json({"error": str(exc)}, status=500)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/crawl":
                payload = self.read_json_body()
                items, errors = fetch_rss(
                    max_items_per_feed=int(payload.get("max_items_per_feed", 8)),
                    source_ids=payload.get("source_ids"),
                    start_date=payload.get("start_date"),
                    end_date=payload.get("end_date"),
                )
                filtered_items, filter_results = filter_news_items(items)
                inserted = database.insert_news_items(filtered_items)
                return self.send_json(
                    {
                        "fetched": len(items),
                        "passed_filter": len(filtered_items),
                        "filtered_out": len(items) - len(filtered_items),
                        "inserted": inserted,
                        "errors": errors,
                        "filter_results": filter_results,
                        "source_ids": payload.get("source_ids") or [],
                        "start_date": payload.get("start_date"),
                        "end_date": payload.get("end_date"),
                    }
                )
            if parsed.path == "/api/reports/generate":
                payload = self.read_json_body()
                result = generate_daily_report(report_date=payload.get("report_date"))
                return self.send_json(result)
            return self.send_json({"error": "not found"}, status=404)
        except Exception as exc:
            return self.send_json({"error": str(exc)}, status=500)

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        if not raw.strip():
            return {}
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}

    def serve_static(self, path: str) -> None:
        if path in {"", "/"}:
            path = "/index.html"
        target = (FRONTEND_DIR / path.lstrip("/")).resolve()
        frontend_root = FRONTEND_DIR.resolve()
        if not str(target).startswith(str(frontend_root)) or not target.exists() or target.is_dir():
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return
        body = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    database.init_db()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Daily AI Insight Engine running at http://127.0.0.1:8000")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
