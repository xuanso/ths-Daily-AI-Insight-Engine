# Agent and Harness Design

## Goal

Daily AI Insight Engine turns recent AI-related news into a structured daily intelligence report. The system is built as a lightweight Harness: each step has a clear input, output, validation boundary, and failure surface.

## Agent Chain

```text
RSS Crawler
-> DataFilterAgent
-> DataCleaningAgent
-> HotspotAgent
-> DeepSummaryAgent
-> TrendAgent
-> RiskOpportunityAgent
-> ValidationAgent
-> Report Renderer
```

## Agents

### DataFilterAgent

Checks whether crawled content is true AI public-opinion news before database insertion.

Filters out:

- Recruiting or job posts
- Course, membership, event, or marketing ads
- Generic technology news unrelated to AI
- Navigation or download pages

### DataCleaningAgent

Extracts structured fields from each validated news item according to the project schema:

- entities
- event_type
- topic_tags
- key_claims
- impact_score
- risks
- opportunities
- analysis_basis

### HotspotAgent

Selects Top 3-5 important AI events from structured records.

### DeepSummaryAgent

Generates background and impact analysis for key events.

### TrendAgent

Generates trend insights across technology, application, policy, capital, and ecosystem dimensions.

### RiskOpportunityAgent

Identifies potential risks and opportunities from structured signals.

### ValidationAgent

Checks whether all agent outputs are well-formed, grounded, and traceable to `news_id`.

## Hooks

- `pre_crawl`: load selected source IDs and date filters.
- `post_crawl`: normalize RSS items.
- `post_filter`: only insert records approved by `DataFilterAgent`.
- `post_cleaning`: persist structured records to SQLite.
- `pre_report`: aggregate structured data for the chosen report date.
- `post_report`: save Markdown and JSON report artifacts.
- `post_validation`: store validation result with the report.

## Skills

- `news_filtering`: reject non-AI, recruiting, ads, and low-information content.
- `structured_extraction`: convert raw news into schema-compliant JSON.
- `hotspot_ranking`: rank events by impact and relevance.
- `trend_analysis`: infer supported trends from structured fields.
- `risk_opportunity_detection`: identify actionable risk and opportunity signals.
- `result_validation`: verify format, completeness, and traceability.

## Design Constraints

- Raw data is never sent to the model as one giant prompt to generate the full report.
- News items are filtered and structured item by item.
- Analysis agents operate on structured data, not raw mixed-source blobs.
- Final reports include validation results and source links.
