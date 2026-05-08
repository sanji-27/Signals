import feedparser
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NewsAgent:
    def __init__(self):
        # Example RSS feeds for economic news
        self.feeds = [
            "https://www.forexlive.com/rss",
            "https://www.investing.com/rss/news.rss"
        ]
        self.keywords = ["CPI", "FED", "Inflation", "NFP", "Rates", "Interest"]

    def get_sentiment(self) -> Dict[str, Any]:
        """Fetch news and check for high-impact keywords."""
        high_impact = False
        latest_titles = []

        for url in self.feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    title = entry.title.upper()
                    latest_titles.append(title)
                    if any(kw in title for kw in self.keywords):
                        high_impact = True
                        break
            except Exception as e:
                logger.error(f"Error fetching news from {url}: {e}")

        return {
            "impact": "high" if high_impact else "low",
            "news_active": high_impact,
            "latest_news": latest_titles[:3]
        }
