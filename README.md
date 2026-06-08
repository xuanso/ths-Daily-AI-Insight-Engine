# Daily AI Insight Engine

AI 舆情分析日报系统 MVP：从公开新闻源爬取 AI 相关新闻，经过 DeepSeek 多 Agent 处理，生成结构化日报和前端可视化结果。

## 快速开始

```bash
cd "Daily AI Insight Engine"
copy .env.example .env
```

在 `.env` 中填写：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

启动：

```bash
python backend/server.py
```

访问：

```text
http://127.0.0.1:8000
```

## 功能

- 按来源和日期范围爬取 AI 新闻。
- 入库前调用 `DataFilterAgent` 过滤招聘、广告、泛科技和非 AI 舆论新闻。
- 使用 SQLite 保存原始新闻、结构化结果和日报。
- 按日期调用 DeepSeek 多 Agent 生成日报。
- 前端支持新闻原文跳转、日报生成、日报查看。

## 数据源说明

系统内置 10 个 RSS 来源，包含英文科技媒体、中文科技媒体和 Google News 近 24 小时聚合源。

英文来源：

- TechCrunch AI
- The Verge AI
- MIT Technology Review
- Google News EN AI 24h
- Google News EN Frontier AI 24h

中文来源：

- 36Kr AI
- 机器之心 AI
- 量子位 AI
- Google News 中文 AI 24h
- Google News 中文前沿 AI 24h

选择理由：

- 科技媒体适合观察 AI 行业、产品、资本和技术动态。
- Google News 24h 聚合源用于补足当天数据，解决普通 RSS 更新慢的问题。
- 中文和英文混合，兼顾国际 AI 趋势和中文产业舆论。
- 不使用微信公众号或 `wechat2rss`。

原始数据字段包括：标题、正文或摘要、来源、来源类型、URL、发布时间、语言。

## 系统设计思路

整体流程：

```text
RSS Crawler
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

关键决策：

- 先筛选再入库，保证数据质量。
- 每条新闻独立结构化，不把原始数据一次性丢给 AI。
- 分析 Agent 只使用结构化数据，避免简单摘要拼接。
- 最终结果由 `ValidationAgent` 校验格式和可追溯性。
- 前端保留原始新闻链接，方便追溯来源。

## AI 使用方式

使用 DeepSeek API，调用位置如下：

- `DataFilterAgent`：判断是否为 AI 舆论新闻。
- `DataCleaningAgent`：按 Schema 抽取结构化字段。
- `HotspotAgent`：生成 Top 3-5 重要事件。
- `DeepSummaryAgent`：生成关键事件背景和影响分析。
- `TrendAgent`：生成技术、应用、政策、资本等趋势判断。
- `RiskOpportunityAgent`：识别风险和机会。
- `ValidationAgent`：校验所有结果是否规范、可追溯。

Prompt 保存在：

```text
backend/prompts/
```

Prompt 设计原则：

- 要求 DeepSeek 输出 JSON。
- 每个 Agent 有独立任务和输出格式。
- 要求结论尽量关联 `news_id`。
- 对筛选 Agent 明确过滤招聘、广告、会员推广和泛科技内容。

错误处理：

- DeepSeek Key 缺失时返回明确错误。
- 单个 RSS 源失败不影响其他来源。
- JSON 解析失败时中断对应流程，避免错误结果静默入库。
- 前端顶部状态栏展示接口错误。

## Schema 设计

`DataCleaningAgent` 输出核心字段：

```json
{
  "news_id": 1,
  "title": "新闻标题",
  "source": "来源",
  "url": "来源链接",
  "published_at": "2026-06-08",
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

设计理由：

- `entities`、`event_type`、`topic_tags` 用于结构化抽取和聚合。
- `impact_score` 用于热点排序。
- `risks`、`opportunities` 支撑风险机会提示。
- `analysis_basis` 方便校验和追溯。

## 核心流程说明

爬取流程：

```text
选择来源和日期
-> 抓取 RSS
-> DataFilterAgent 筛选
-> 写入 news 表
```

日报生成流程：

```text
选择日报日期
-> 查询当日新闻
-> DataCleaningAgent 结构化
-> 多 Agent 分析
-> ValidationAgent 校验
-> 保存 Markdown / JSON
```

前端查看流程：

```text
GET /api/reports
-> GET /api/reports/{id}
-> 展示摘要、Markdown、JSON
```

## 输出示例

已生成示例：

- `data/raw_news_2026-06-08.json`
- `data/structured_news_2026-06-08.json`
- `data/reports/report_5.md`
- `data/reports/report_5.json`

示例日报验证结果：

```text
report_date: 2026-06-08
news_count: 15
hotspots: 5
valid: True
```

## 项目结构

```text
Daily AI Insight Engine/
├── backend/
│   ├── agents/
│   ├── services/
│   ├── prompts/
│   └── server.py
├── frontend/
├── data/
├── docs/
├── agent.md
└── README.md
```

## API

```text
GET  /api/sources
POST /api/crawl
GET  /api/news
POST /api/reports/generate
GET  /api/reports
GET  /api/reports/{id}
```
