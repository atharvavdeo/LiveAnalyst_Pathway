# OPML Mass Ingestion Connector for Pathway
# This is the "nuclear option" - ingesting 1800+ feeds from OPML files

import pathway as pw
import requests
import feedparser
import time
import random
import re


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
        """Extracts xmlUrls from OPML content using regex (lenient parsing)"""
        try:
            # Decode content if bytes
            text = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else content
            
            # Use regex to find all xmlUrl attributes (handles malformed XML)
            pattern = r'xmlUrl="([^"]+)"[^>]*(?:text="([^"]*)")?'
            matches = re.findall(pattern, text)
            
            for match in matches:
                url = match[0]
                category = match[1] if len(match) > 1 and match[1] else "General"
                if url and url.startswith('http'):
                    self.feed_urls.add((url, category))
                    
            # Also try alternate pattern
            pattern2 = r'<outline[^>]+xmlUrl="([^"]+)"[^>]*>'
            for url_match in re.finditer(pattern2, text):
                url = url_match.group(1)
                if url and url.startswith('http'):
                    self.feed_urls.add((url, "RSS"))
                    
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
        
        if not self.feed_urls:
            print("⚠️ OPML: No feeds loaded, streaming disabled.")
            while True:
                yield None  # Keep generator alive
                time.sleep(3600)
        
        print(f"🚀 OPML: Starting to parse {len(self.feed_urls)} RSS feeds...")
        
        while True:
            # Convert set to list and shuffle to avoid hammering one server
            feeds = list(self.feed_urls)
            random.shuffle(feeds)
            items_yielded = 0

            for idx, (url, category) in enumerate(feeds):
                try:
                    # Parse the individual RSS feed with timeout
                    feed = feedparser.parse(url)
                    
                    if not feed.entries:
                        continue
                    
                    # Process top 3 entries to keep latency low
                    for entry in feed.entries[:3]:
                        if hasattr(entry, 'link') and entry.link not in self.seen_entries:
                            self.seen_entries.add(entry.link)
                            items_yielded += 1
                            
                            # Log progress every 10 items
                            if items_yielded % 10 == 0:
                                print(f"📰 OPML: Yielded {items_yielded} items so far...")
                            
                            # Yield normalized schema for Pathway
                            yield {
                                "text": f"{entry.get('title', 'Untitled')} - {entry.get('summary', '')[:300]}",
                                "source": "opml",  # Consistent source name for filtering
                                "category": category,
                                "url": entry.link,
                                "reliability": "High",  # RSS is generally reliable
                                "created_utc": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                                "feed_title": feed.feed.get('title', 'Unknown')
                            }
                except Exception as e:
                    continue  # Skip broken feeds
                
                # Tiny sleep to be a "polite" crawler
                time.sleep(0.05)  # Reduced from 0.1

            print(f"✅ OPML: Completed cycle, yielded {items_yielded} new items. Sleeping {self.poll_frequency}s...")
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


# Default OPML sources from awesome-rss-feeds repository (correct paths)
DEFAULT_OPML_URLS = [
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/without_category/Tech.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/without_category/Programming.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/without_category/News.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/without_category/Science.opml",
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
