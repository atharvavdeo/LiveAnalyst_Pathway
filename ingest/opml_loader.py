# OPML Mass Ingestion Connector for Pathway
# This is the "nuclear option" - ingesting 1800+ feeds from OPML files

# import pathway as pw
import requests
import feedparser
import time
import random
import re


class OPMLIngestor:
    """
    Pathway Connector that ingests RSS feeds from OPML files.
    Designed for high-volume ingestion from repositories like plenaryapp/awesome-rss-feeds.
    """
    
    def __init__(self, opml_urls, poll_frequency=300):
        # super().__init__()
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
        print(f"✅ Loaded {len(self.feed_urls)} active feeds from OPML.")

    def manual_refresh(self):
        """Trigger an immediate restart of the fetching loop with BURST SPEED."""
        print("⚡ OPML: Manual refresh signal received! Activating BURST MODE.")
        
        # CRITICAL: Clear seen_entries to allow re-yielding recent articles
        print(f"🧹 Clearing {len(self.seen_entries)} seen entries to allow fresh fetch")
        self.seen_entries.clear()
        
        self.force_restart = True
        self.burst_mode = True # Activate burst mode

    def run(self):
        # Initial Load
        self._refresh_sources()
        self.seen_entries = set()
        self.force_restart = False
        self.burst_mode = False # Add burst mode flag
        
        if not self.feed_urls:
            print("⚠️ OPML: No feeds loaded, streaming disabled.")
            while True:
                yield None  # Keep generator alive
                time.sleep(3600)
        
        print(f"🚀 OPML: Starting to parse {len(self.feed_urls)} RSS feeds...")
        
        while True:
            # CRITICAL: Clear seen_entries at start of EVERY cycle to re-yield recent articles
            # This ensures fresh display on every scan, not just on manual refresh
            print(f"🧹 Clearing {len(self.seen_entries)} seen entries from previous cycle")
            self.seen_entries.clear()
            
            # Convert to list and shuffle to avoid hammering one server
            feeds = list(self.feed_urls)
            random.shuffle(feeds)
            items_yielded = 0
            
            # Reset flag at start of cycle
            if self.force_restart:
                self.force_restart = False

            for idx, (url, category) in enumerate(feeds):
                # CHECK FOR MANUAL INTERRUPT
                if self.force_restart:
                    print("⚡ OPML: Restarting feed cycle immediately...")
                    break

                # MAXIMUM SPEED: Always 0s sleep for real-time updates
                sleep_time = 0.0

                try:
                    # Parse the individual RSS feed with timeout
                    # feedparser handles timeouts internally or via socket default?
                    # Set global socket timeout if needed, but requests uses its own.
                    # Feedparser uses urllib.
                    feed = feedparser.parse(url)
                    
                    if not feed.entries:
                        continue
                    
                    # Process top 3 entries to keep latency low
                    for entry in feed.entries[:3]:
                        if hasattr(entry, 'link') and entry.link not in self.seen_entries:
                            # Get ACTUAL publication date from RSS
                            pub_date = None
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry.published_parsed)
                            elif hasattr(entry, 'published') and entry.published:
                                pub_date = entry.published
                            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                                pub_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry.updated_parsed)
                            else:
                                # No date found = SKIP this article (don't fake it as "now")
                                # print(f"⚠️ Skipping article with no date: {entry.get('title', 'Unknown')}")
                                continue
                            
                            
                            # === FRESHNESS FILTER DISABLED ===
                            # RSS feeds update slowly (15-60min). Strict time filters result in 0 new articles.
                            # Let frontend handle sorting/filtering instead.
                            # Backend yields ALL recent articles for maximum coverage.
                            
                            
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
                                "created_utc": pub_date,
                                "feed_title": feed.feed.get('title', 'Unknown')
                            }
                except Exception as e:
                    # print(f"⚠️ Error processing feed {url}: {e}") # Optional: uncomment for debugging
                    continue  # Skip broken feeds
                
                # Tiny sleep to be a "polite" crawler (or 0 if BURST)
                time.sleep(sleep_time)  

            # === BURST MODE LOGIC ===
            # If burst mode was active, turn it off after one full cycle
            if self.burst_mode:
                print(f"🏁 OPML: Burst cycle complete. Returning to polite mode (sleep={self.poll_frequency}s).")
                self.burst_mode = False
            
            print(f"✅ OPML: Completed cycle, yielded {items_yielded} new items. Sleeping...")
            
            # Interruptible Sleep (Check every 0.1s for manual refresh)
            sleep_target = self.poll_frequency
            # If burst mode just triggered (unlikely here, usually set in manual_refresh), skip sleep
            if self.burst_mode: 
                sleep_target = 0
                
            for _ in range(int(sleep_target * 10)):
                if self.force_restart:
                    print("⚡ OPML: Waking up early due to manual refresh!")
                    break
                time.sleep(0.1)


# Pathway Schema for OPML items
# class OPMLSchema(pw.Schema):
#     text: str
#     source: str
#     category: str
#     url: str
#     reliability: str
#     timestamp: float


# Default OPML sources from awesome-rss-feeds repository
# Uses regex parsing to handle malformed XML in OPML files
DEFAULT_OPML_URLS = [
    # === COMPREHENSIVE OPML LIST - ALL CATEGORIES ===
    #With categories:
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Android Development.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Android.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Apple.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Architecture.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Beauty.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Books.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Business & Economy.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Cars.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Cricket.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/DIY.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Fashion.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Food.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Football.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Funny.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Gaming.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/History.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Interior design.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Movies.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Music.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/News.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Personal finance.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Photography.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Programming.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Science.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Space.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Sports.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Startups.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Tech.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Television.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Tennis.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Travel.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/UI - UX.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Web Development.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/iOS Development.opml",
]


def create_opml_table(opml_urls=None):
    """
    Factory function to create a Pathway table from OPML feeds.
    """
    pass
    # urls = opml_urls or DEFAULT_OPML_URLS
    # return pw.io.python.read(
    #     OPMLIngestor(opml_urls=urls),
    #     schema=OPMLSchema
    # )
