from __future__ import annotations

from typing import Any

from backend.agents.base import Agent, ensure_list


class TrendAgent(Agent):
    name = "trend_agent"

    def run(self, structured_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        system = """你是趋势判断 Agent。请输出技术、应用、政策、资本方向的趋势洞察。
只输出 JSON: {"trends": [{"dimension": "技术/应用/政策/资本/生态", "insight": "", "supporting_news_ids": [], "confidence": "high/medium/low"}]}。
要求：趋势必须有结构化数据支撑。"""
        result = self.call_json(system, {"structured_items": structured_items}, temperature=0.25)
        return ensure_list(result.get("trends"))

