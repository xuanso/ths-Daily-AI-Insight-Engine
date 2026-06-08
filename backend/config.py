from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "daily_ai_insight.db"
FRONTEND_DIR = ROOT_DIR / "frontend"


def load_env_file() -> None:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lstrip("\ufeff")
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))


load_env_file()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

# Three English sources and three Chinese sources. Chinese sources use Google News
# site-search RSS for public websites, not WeChat public-account feeds.
RSS_FEEDS = [
    {
        "id": "techcrunch_ai",
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "source_type": "media",
        "language": "en",
    },
    {
        "id": "the_verge_ai",
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "source_type": "media",
        "language": "en",
    },
    {
        "id": "mit_technology_review",
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "source_type": "media",
        "language": "en",
    },
    {
        "id": "google_news_en_ai_1d",
        "name": "Google News EN AI 24h",
        "url": "https://news.google.com/rss/search?q=artificial%20intelligence%20when:1d&hl=en-US&gl=US&ceid=US:en",
        "source_type": "aggregator",
        "language": "en",
    },
    {
        "id": "google_news_en_frontier_ai_1d",
        "name": "Google News EN Frontier AI 24h",
        "url": "https://news.google.com/rss/search?q=OpenAI%20OR%20Anthropic%20OR%20Google%20AI%20when:1d&hl=en-US&gl=US&ceid=US:en",
        "source_type": "aggregator",
        "language": "en",
    },
    {
        "id": "36kr_ai",
        "name": "36Kr AI",
        "url": "https://news.google.com/rss/search?q=AI%20site:36kr.com&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "source_type": "media",
        "language": "zh",
    },
    {
        "id": "jiqizhixin_ai",
        "name": "机器之心 AI",
        "url": "https://news.google.com/rss/search?q=AI%20site:jiqizhixin.com&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "source_type": "media",
        "language": "zh",
    },
    {
        "id": "qbitai_ai",
        "name": "量子位 AI",
        "url": "https://news.google.com/rss/search?q=AI%20site:qbitai.com&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "source_type": "media",
        "language": "zh",
    },
    {
        "id": "google_news_zh_ai_1d",
        "name": "Google News 中文 AI 24h",
        "url": "https://news.google.com/rss/search?q=%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%20OR%20%E5%A4%A7%E6%A8%A1%E5%9E%8B%20when:1d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "source_type": "aggregator",
        "language": "zh",
    },
    {
        "id": "google_news_zh_frontier_ai_1d",
        "name": "Google News 中文前沿 AI 24h",
        "url": "https://news.google.com/rss/search?q=OpenAI%20OR%20DeepSeek%20OR%20Anthropic%20OR%20%E5%A4%A7%E6%A8%A1%E5%9E%8B%20when:1d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "source_type": "aggregator",
        "language": "zh",
    },
]
