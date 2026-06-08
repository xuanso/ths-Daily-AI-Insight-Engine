# Harness Engineering 说明

系统将日报生成拆为可观测、可校验的 Agent 链路：

```text
Crawler
-> DataFilterAgent
-> SQLite news
-> DataCleaningAgent
-> SQLite structured_news
-> HotspotAgent
-> DeepSummaryAgent
-> TrendAgent
-> RiskOpportunityAgent
-> ValidationAgent
-> SQLite reports
-> Frontend Dashboard
```

## Hooks

- `pre_crawl`：统一 RSS 源配置。
- `post_crawl`：调用 DataFilterAgent，过滤招聘、广告、泛科技和非 AI 舆论新闻。
- `post_filter`：只把通过筛选的数据去重写入 SQLite。
- `post_cleaning`：结构化结果落库。
- `pre_report`：取最近新闻作为样本。
- `post_report`：写入 `reports` 表并导出 Markdown/JSON。
- `post_validation`：保存校验结果。

## 关键约束

- 不把原始数据一次性丢给 AI 生成完整日报。
- 不从微信公众平台或 `wechat2rss` 获取数据。
- 爬取数据必须经过 DataFilterAgent 校验后才能入库。
- 数据清洗逐条调用 DeepSeek。
- 分析 Agent 只接收结构化数据。
- 结果校验 Agent 必须检查输出格式和 news_id 可追溯性。
