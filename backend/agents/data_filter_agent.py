from __future__ import annotations

from typing import Any

from backend.agents.base import Agent, ensure_str


class DataFilterAgent(Agent):
    name = "data_filter_agent"

    def run(self, news: dict[str, Any]) -> dict[str, Any]:
        system = """你是 AI 舆论新闻筛选 Agent。请判断输入内容是否应该进入 AI 舆情分析日报数据库。
只输出 JSON，不要输出解释。

输出格式:
{
  "is_ai_opinion_news": true,
  "category": "AI新闻/招聘/广告/会员课程/泛科技/无关",
  "confidence": "high/medium/low",
  "reason": "一句话说明判断依据"
}

必须过滤掉:
- 招聘、岗位、人才招聘、实习招聘
- 会员推广、课程广告、活动广告、下载页、导航页
- 与 AI 无关的泛科技新闻
- 只有公司促销、营销话术、没有新闻事实的信息

允许通过:
- AI 模型、产品、公司、政策、安全、资本、研究、应用、舆论争议相关新闻
- 中文或英文 AI 行业新闻
"""
        result = self.call_json(system, {"news": news}, temperature=0)
        return {
            "is_ai_opinion_news": bool(result.get("is_ai_opinion_news", False)),
            "category": ensure_str(result.get("category"), "unknown"),
            "confidence": ensure_str(result.get("confidence"), "low"),
            "reason": ensure_str(result.get("reason"), "未给出原因"),
        }
