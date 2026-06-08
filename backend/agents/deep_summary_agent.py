from __future__ import annotations

from typing import Any

from backend.agents.base import Agent, ensure_list


class DeepSummaryAgent(Agent):
    name = "deep_summary_agent"

    def run(self, structured_items: list[dict[str, Any]], hotspots: list[dict[str, Any]]) -> list[dict[str, Any]]:
        system = """你是重要事件深度总结 Agent。请对关键事件做背景+影响分析。
只输出 JSON: {"deep_summaries": [{"title": "", "background": "", "impact": "", "evidence_news_ids": []}]}。
要求：每条总结必须引用输入中的 news_id，避免空泛判断。"""
        result = self.call_json(
            system,
            {"structured_items": structured_items, "hotspots": hotspots},
            temperature=0.25,
        )
        return ensure_list(result.get("deep_summaries"))

