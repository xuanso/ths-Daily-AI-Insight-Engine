from __future__ import annotations

from typing import Any

from backend.agents.base import Agent, ensure_list


class HotspotAgent(Agent):
    name = "hotspot_agent"

    def run(self, structured_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        system = """你是今日 AI 领域主要热点 Agent。请从结构化新闻中选出 Top 3-5 重要事件。
只输出 JSON: {"hotspots": [{"rank": 1, "title": "", "news_ids": [], "reason": "", "impact_score": 1-10, "tags": []}]}。
要求：必须基于输入中的 impact_score、事件类型、来源可信度和主题聚合判断。"""
        result = self.call_json(system, {"structured_items": structured_items}, temperature=0.2)
        hotspots = ensure_list(result.get("hotspots"))
        return hotspots[:5]

