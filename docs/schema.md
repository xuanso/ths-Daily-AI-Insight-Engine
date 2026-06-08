# 新闻结构化 Schema

`DataCleaningAgent` 输出结构：

```json
{
  "news_id": 1,
  "title": "新闻标题",
  "source": "来源",
  "url": "来源链接",
  "published_at": "2026-06-07",
  "entities": {
    "companies": [],
    "people": [],
    "products": [],
    "models": [],
    "technologies": []
  },
  "event_type": "model_release",
  "topic_tags": [],
  "key_claims": [],
  "impact_score": 8,
  "impact_level": "high",
  "sentiment": "positive",
  "affected_sectors": [],
  "risks": [],
  "opportunities": [],
  "structured_summary": "结构化摘要",
  "analysis_basis": "评分和分类依据"
}
```

## 设计理由

- `entities`：识别事件主体，便于聚合公司、模型和产品。
- `event_type`：把新闻变成可统计的事件。
- `topic_tags`：支撑热点聚合和趋势判断。
- `impact_score` / `impact_level`：支撑 Top 事件排序。
- `risks` / `opportunities`：直接服务风险机会 Agent。
- `analysis_basis`：保留判断依据，便于结果校验 Agent 追溯。

