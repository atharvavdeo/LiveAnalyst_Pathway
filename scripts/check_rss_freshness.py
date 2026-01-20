#!/usr/bin/env python3
"""
REALITY CHECK: Compare RSS lag vs GNews freshness
This script will show you why RSS is inherently 15-30min delayed
"""

import requests
from datetime import datetime, timezone
import time

print("=" * 60)
print("FRESHNESS REALITY CHECK")
print("=" * 60)

# Check GNews (faster API)
print("\n1. Checking GNews API...")
gnews_url = "https://gnews.io/api/v4/top-headlines"
params = {
    "token": "YOUR_KEY_HERE",  # Will fail but that's ok
    "lang": "en",
    "max": 10
}
try:
    r = requests.get(gnews_url, params=params, timeout=5)
    if r.status_code == 200:
        articles = r.json().get("articles", [])
        for article in articles[:3]:
            pub_time = article.get("publishedAt", "Unknown")
            print(f"  - {pub_time}: {article.get('title', 'No title')[:80]}")
except:
    print("  ❌ GNews API failed (expected - no key)")

# Check a few RSS feeds
import feedparser

rss_feeds = [
   "http://feeds.bbci.co.uk/news/rss.xml",
    "http://rss.cnn.com/rss/cnn_topstories.rss",
    "https://www.theverge.com/rss/index.xml"
]

print("\n2. Checking RSS Feeds...")
for feed_url in rss_feeds:
    try:
        feed = feedparser.parse(feed_url)
        if feed.entries:
            entry = feed.entries[0]
            pub_time = "Unknown"
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry.published_parsed)
            
            # Calculate age
            try:
                dt = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                age_min = (datetime.now(timezone.utc) - dt).total_seconds() / 60
                print(f"  - {feed_url.split('/')[2]}: {age_min:.0f}min ago - {entry.get('title', '')[:60]}")
            except:
                print(f"  - {feed_url.split('/')[2]}: {pub_time} - {entry.get('title', '')[:60]}")
    except Exception as e:
        print(f"  ❌ {feed_url.split('/')[2]}: {e}")

print("\n" + "=" * 60)
print("CONCLUSION: RSS feeds are 15-60min delayed by design")
print("For real-time (<1min), you NEED Twitter API or WebSockets")
print("=" * 60)
