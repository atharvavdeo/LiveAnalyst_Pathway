# OPML Mass Ingestion Connector for Pathway
# This is the "nuclear option" - ingesting 1800+ feeds from OPML files

import pathway as pw
import requests
import feedparser
import time
import random
import defusedxml.ElementTree as ET
from io import BytesIO


class OPMLIngestor(pw.io.python.ConnectorSubject):
    """
    Pathway Connector that ingests RSS feeds from OPML files.
    Designed for high-volume ingestion from repositories like plenaryapp/awesome-rss-feeds.
    """
    
    def __init__(self, opml_urls, poll_frequency=300):
        super().__init__()
        self.opml_urls = opml_urls
        self.poll_frequency = poll_frequency  # Poll feeds every 5 mins
        self.feed_urls = set()
        self.seen_entries = set()

    def _parse_opml(self, content):
        """Recursively extracts xmlUrls from OPML content"""
        try:
            tree = ET.parse(BytesIO(content))
            root = tree.getroot()
            # Find all 'outline' elements with an 'xmlUrl' attribute
            for outline in root.findall(".//outline[@xmlUrl]"):
                url = outline.get("xmlUrl")
                category = outline.get("text") or outline.get("title") or "General"
                if url:
                    self.feed_urls.add((url, category))
        except Exception as e:
            print(f"⚠️ OPML Parse Error: {e}")

    def _refresh_sources(self):
        """Fetches the latest OPML lists from GitHub"""
        print(f"🔄 Refreshing source lists from {len(self.opml_urls)} OPML files...")
        for url in self.opml_urls:
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    self._parse_opml(resp.content)
            except Exception as e:
                print(f"❌ Failed to fetch OPML {url}: {e}")
        print(f"✅ Loaded {len(self.feed_urls)} active feeds.")

    def run(self):
        # Initial Load
        self._refresh_sources()
        
        while True:
            # Convert set to list and shuffle to avoid hammering one server
            feeds = list(self.feed_urls)
            random.shuffle(feeds)

            for url, category in feeds:
                try:
                    # Parse the individual RSS feed
                    feed = feedparser.parse(url)
                    
                    # Process top 3 entries to keep latency low
                    for entry in feed.entries[:3]:
                        if entry.link not in self.seen_entries:
                            self.seen_entries.add(entry.link)
                            
                            # Yield normalized schema for Pathway
                            yield {
                                "text": f"{entry.title} - {entry.get('summary', '')[:300]}",
                                "source": feed.feed.get('title', 'Unknown Source'),
                                "category": category,
                                "url": entry.link,
                                "reliability": "High",  # RSS is generally reliable
                                "timestamp": time.time()
                            }
                except Exception:
                    continue  # Skip broken feeds
                
                # Tiny sleep to be a "polite" crawler
                time.sleep(0.1)

            # Wait before restarting the massive loop
            time.sleep(self.poll_frequency)


# Pathway Schema for OPML items
class OPMLSchema(pw.Schema):
    text: str
    source: str
    category: str
    url: str
    reliability: str
    timestamp: float


# Default OPML sources from awesome-rss-feeds repository
DEFAULT_OPML_URLS = [
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/categories/programming.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/categories/technology.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/categories/news.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/categories/science.opml",
]


def create_opml_table(opml_urls=None):
    """
    Factory function to create a Pathway table from OPML feeds.
    """
    urls = opml_urls or DEFAULT_OPML_URLS
    return pw.io.python.read(
        OPMLIngestor(opml_urls=urls),
        schema=OPMLSchema
    )
