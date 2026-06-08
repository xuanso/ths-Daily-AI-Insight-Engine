from __future__ import annotations

from typing import Any

from backend.agents.base import Agent, ensure_list, ensure_str


EVENT_TYPES = {
    "model_release",
    "product_update",
    "developer_tooling",
    "capital_market",
    "policy_safety",
    "research",
    "application_case",
    "ecosystem_signal",
}


class DataCleaningAgent(Agent):
    name = "data_cleaning_agent"

    def run(self, news: dict[str, Any]) -> dict[str, Any]:
        system = """你是数据清洗 Agent。请基于结构化 Schema 对单条 AI 新闻进行抽取和整理。
只输出 JSON，不要输出解释。

Schema:
{
  "entities": {"companies": [], "people": [], "products": [], "models": [], "technologies": []},
  "event_type": "model_release/product_update/developer_tooling/capital_market/policy_safety/research/application_case/ecosystem_signal",
  "topic_tags": [],
  "key_claims": [],
  "impact_score": 1-10,
  "impact_level": "high/medium/low",
  "sentiment": "positive/neutral/cautious/negative",
  "affected_sectors": [],
  "risks": [],
  "opportunities": [],
  "structured_summary": "不超过120字",
  "analysis_basis": "说明评分和分类依据"
}

要求:
- 不要只做 summary，必须抽取实体、事件类型、主题、影响、风险机会。
- 所有内容必须来自输入新闻，不确定则给空数组。
"""
        payload = self.call_json(system, {"news": news}, temperature=0.1)
        return normalize_structured(news, payload)


def normalize_structured(news: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    entities = payload.get("entities") if isinstance(payload.get("entities"), dict) else {}
    event_type = ensure_str(payload.get("event_type"), "ecosystem_signal")
    if event_type not in EVENT_TYPES:
        event_type = "ecosystem_signal"
    impact_score = payload.get("impact_score", 5)
    try:
        impact_score = int(impact_score)
    except Exception:
        impact_score = 5
    impact_score = max(1, min(10, impact_score))
    impact_level = ensure_str(payload.get("impact_level"))
    if impact_level not in {"high", "medium", "low"}:
        impact_level = "high" if impact_score >= 8 else "medium" if impact_score >= 5 else "low"
    sentiment = ensure_str(payload.get("sentiment"), "neutral")
    if sentiment not in {"positive", "neutral", "cautious", "negative"}:
        sentiment = "neutral"
    return {
        "news_id": news["id"],
        "title": news["title"],
        "source": news["source"],
        "url": news["url"],
        "published_at": news["published_at"],
        "entities": {
            "companies": ensure_list(entities.get("companies")),
            "people": ensure_list(entities.get("people")),
            "products": ensure_list(entities.get("products")),
            "models": ensure_list(entities.get("models")),
            "technologies": ensure_list(entities.get("technologies")),
        },
        "event_type": event_type,
        "topic_tags": ensure_list(payload.get("topic_tags"), ["AI"]),
        "key_claims": ensure_list(payload.get("key_claims"), [news["content"][:160]]),
        "impact_score": impact_score,
        "impact_level": impact_level,
        "sentiment": sentiment,
        "affected_sectors": ensure_list(payload.get("affected_sectors")),
        "risks": ensure_list(payload.get("risks")),
        "opportunities": ensure_list(payload.get("opportunities")),
        "structured_summary": ensure_str(payload.get("structured_summary"), news["content"][:160]),
        "analysis_basis": ensure_str(payload.get("analysis_basis"), "基于来源、主题和事件类型综合判断。"),
    }

