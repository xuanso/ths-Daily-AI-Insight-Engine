from __future__ import annotations

from typing import Any

from backend.agents.base import Agent, ensure_list


class ValidationAgent(Agent):
    name = "validation_agent"

    def run(self, report_payload: dict[str, Any]) -> dict[str, Any]:
        system = """你是结果校验 Agent。请校验所有 agent 的生成结果是否规范正确。
只输出 JSON: {"valid": true/false, "errors": [], "warnings": [], "fix_suggestions": []}。
校验点：
1. structured_items 是否有 Schema 必填字段。
2. hotspots 是否为 Top 3-5。
3. deep_summaries 是否包含背景和影响。
4. trends 是否覆盖技术/应用/政策/资本中的至少两个方向。
5. risks/opportunities 是否有 level 和依据。
6. 所有分析是否能追溯到 news_id。"""
        result = self.call_json(system, report_payload, temperature=0)
        return {
            "valid": bool(result.get("valid", False)),
            "errors": ensure_list(result.get("errors")),
            "warnings": ensure_list(result.get("warnings")),
            "fix_suggestions": ensure_list(result.get("fix_suggestions")),
        }

