from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from backend.agents.cleaning_agent import DataCleaningAgent
from backend.agents.deep_summary_agent import DeepSummaryAgent
from backend.agents.hotspot_agent import HotspotAgent
from backend.agents.risk_opportunity_agent import RiskOpportunityAgent
from backend.agents.trend_agent import TrendAgent
from backend.agents.validation_agent import ValidationAgent
from backend.services import database
from backend.services.deepseek_client import DeepSeekClient


def generate_markdown(report: dict[str, Any], validation: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        f"报告日期：{report['report_date']}",
        f"样本数量：{report['summary']['news_count']} 条",
        "",
        "## 信息结构化结果",
        "",
        "| ID | 标题 | 来源 | 事件类型 | 影响分 | 主题 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["structured_items"]:
        lines.append(
            f"| {item['news_id']} | {item['title']} | {item['source']} | "
            f"{item['event_type']} | {item['impact_score']} | {', '.join(item['topic_tags'])} |"
        )
    lines.extend(["", "## 今日 AI 领域主要热点", ""])
    for item in report["hotspots"]:
        lines.append(f"### {item.get('rank', '-')}. {item.get('title', '')}")
        lines.append(f"- 原因：{item.get('reason', '')}")
        lines.append(f"- 关联新闻：{', '.join(map(str, item.get('news_ids', [])))}")
        lines.append("")
    lines.extend(["## 重要事件深度总结", ""])
    for item in report["deep_summaries"]:
        lines.append(f"### {item.get('title', '')}")
        lines.append(f"- 背景：{item.get('background', '')}")
        lines.append(f"- 影响：{item.get('impact', '')}")
        lines.append("")
    lines.extend(["## 趋势判断", ""])
    for item in report["trends"]:
        lines.append(f"- **{item.get('dimension', '')}**：{item.get('insight', '')}")
    lines.extend(["", "## 风险或机会提示", "", "### 风险"])
    for item in report["risk_opportunity"]["risks"]:
        lines.append(f"- [{item.get('level', '')}] {item.get('title', '')}：{item.get('detail', '')}")
    lines.append("")
    lines.append("### 机会")
    for item in report["risk_opportunity"]["opportunities"]:
        lines.append(f"- [{item.get('level', '')}] {item.get('title', '')}：{item.get('detail', '')}")
    lines.extend(["", "## 结果校验", ""])
    lines.append(f"- 是否通过：{validation['valid']}")
    lines.append(f"- 错误：{'; '.join(validation['errors']) or '无'}")
    lines.append(f"- 警告：{'; '.join(validation['warnings']) or '无'}")
    lines.extend(["", "## 来源链接", ""])
    for item in report["structured_items"]:
        lines.append(f"- [{item['news_id']}] [{item['title']}]({item['url']})")
    return "\n".join(lines) + "\n"


def build_summary(structured_items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "news_count": len(structured_items),
        "source_count": dict(Counter(item["source"] for item in structured_items)),
        "event_type_count": dict(Counter(item["event_type"] for item in structured_items)),
        "topic_count": dict(Counter(tag for item in structured_items for tag in item["topic_tags"])),
        "average_impact_score": round(sum(item["impact_score"] for item in structured_items) / max(len(structured_items), 1), 2),
    }


def generate_daily_report(report_date: str | None = None, limit: int = 15) -> dict[str, Any]:
    client = DeepSeekClient()
    if not client.available:
        raise RuntimeError("DEEPSEEK_API_KEY is required to generate reports")

    selected_date = report_date or date.today().isoformat()
    news_items = database.list_news_by_date(selected_date, limit) if report_date else database.list_recent_news(limit)
    if not news_items:
        raise RuntimeError(f"No news in database for {selected_date}. Please crawl data first.")

    cleaning_agent = DataCleaningAgent(client)
    structured_items = []
    for news in news_items:
        structured = cleaning_agent.run(news)
        database.upsert_structured(news["id"], structured)
        structured_items.append(structured)

    hotspot_agent = HotspotAgent(client)
    deep_summary_agent = DeepSummaryAgent(client)
    trend_agent = TrendAgent(client)
    risk_opportunity_agent = RiskOpportunityAgent(client)
    validation_agent = ValidationAgent(client)

    hotspots = hotspot_agent.run(structured_items)
    deep_summaries = deep_summary_agent.run(structured_items, hotspots)
    trends = trend_agent.run(structured_items)
    risk_opportunity = risk_opportunity_agent.run(structured_items)

    report = {
        "title": "AI 舆情分析日报",
        "report_date": selected_date,
        "summary": build_summary(structured_items),
        "structured_items": structured_items,
        "hotspots": hotspots,
        "deep_summaries": deep_summaries,
        "trends": trends,
        "risk_opportunity": risk_opportunity,
        "agents": [
            cleaning_agent.name,
            hotspot_agent.name,
            deep_summary_agent.name,
            trend_agent.name,
            risk_opportunity_agent.name,
            validation_agent.name,
        ],
    }
    validation = validation_agent.run(report)
    markdown = generate_markdown(report, validation)
    report_id = database.insert_report(report["report_date"], report["title"], report, markdown, validation)
    database.export_report_files(report_id, markdown, report)
    return {"id": report_id, "report": report, "markdown": markdown, "validation": validation}
