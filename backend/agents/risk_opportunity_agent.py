from __future__ import annotations

from typing import Any

from backend.agents.base import Agent, ensure_list


class RiskOpportunityAgent(Agent):
    name = "risk_opportunity_agent"

    def run(self, structured_items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        system = """你是风险或机会提示 Agent。请识别潜在风险和投资/产品机会。
只输出 JSON: {"risks": [{"title": "", "detail": "", "level": "high/medium/low", "news_ids": []}], "opportunities": [{"title": "", "detail": "", "level": "high/medium/low", "news_ids": []}]}。
要求：不要给投资建议，只识别信号和可能影响。"""
        result = self.call_json(system, {"structured_items": structured_items}, temperature=0.25)
        return {
            "risks": ensure_list(result.get("risks")),
            "opportunities": ensure_list(result.get("opportunities")),
        }

