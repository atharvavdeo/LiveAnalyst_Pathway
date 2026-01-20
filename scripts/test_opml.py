#!/usr/bin/env python3
"""
TEST SCRIPT: Debug OPML Data Fetching
This directly tests OPML ingestion without the full backend
"""

import requests
import feedparser
import time
import re

# OPML sources
DEFAULT_OPML_URLS = [
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Technology.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Programming.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/News.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/with_category/Science.opml",
    "https://raw.githubusercontent.com/plenaryapp/awesome-rss-feeds/master/recommended/without_category/Tech.opml",
]

def parse_opml(content):
    """Extracts xmlUrls from OPML content using regex"""
    feed_urls = set()
    try:
        text = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else content
        pattern = r'xmlUrl="([^"]+)"[^>]*(?:text="([^"]*)")?'
        matches = re.findall(pattern, text)
        
        for match in matches:
            url = match[0]
            category = match[1] if len(match) > 1 and match[1] else "General"
            if url and url.startswith('http'):
                feed_urls.add((url, category))
                
    except Exception as e:
        print(f"⚠️ OPML Parse Error: {e}")
    
    return feed_urls

def main():
    print("="*60)
    print("🧪 OPML FETCH TEST - Direct Terminal Output")
    print("="*60)
    
    all_feeds = set()
    
    # Step 1: Fetch all OPML files
    print("\n📥 STEP 1: Fetching OPML source files...")
    for i, url in enumerate(DEFAULT_OPML_URLS):
        try:
            print(f"  [{i+1}/{len(DEFAULT_OPML_URLS)}] Fetching: {url.split('/')[-1]}")
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                feeds = parse_opml(resp.content)
                all_feeds.update(feeds)
                print(f"      ✅ Got {len(feeds)} feeds from this file")
            else:
                print(f"      ❌ HTTP {resp.status_code}")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    print(f"\n📊 Total unique feeds loaded: {len(all_feeds)}")
    
    if not all_feeds:
        print("❌ NO FEEDS LOADED! Check your internet connection or OPML URLs.")
        return
    
    # Step 2: Test fetching some RSS feeds
    print("\n📰 STEP 2: Testing RSS feed parsing (first 10 feeds)...")
    feeds_list = list(all_feeds)[:10]
    
    successful = 0
    failed = 0
    articles = []
    
    for url, category in feeds_list:
        try:
            print(f"\n  🔍 Parsing: {url[:60]}...")
            feed = feedparser.parse(url)
            
            if not feed.entries:
                print(f"      ⚠️ No entries found")
                failed += 1
                continue
            
            print(f"      ✅ Found {len(feed.entries)} entries")
            successful += 1
            
            # Get first entry
            entry = feed.entries[0]
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry.published_parsed)
            elif hasattr(entry, 'published'):
                pub_date = entry.published
            else:
                pub_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            
            article = {
                "title": entry.get('title', 'Untitled'),
                "url": entry.get('link', 'N/A'),
                "published": pub_date,
                "category": category,
                "source": "opml"
            }
            articles.append(article)
            
            print(f"      📄 Title: {article['title'][:50]}...")
            print(f"      📅 Published: {article['published']}")
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    print(f"  ✅ Successful feeds: {successful}")
    print(f"  ❌ Failed feeds: {failed}")
    print(f"  📰 Articles fetched: {len(articles)}")
    
    if articles:
        print("\n📰 SAMPLE ARTICLES:")
        print("-"*60)
        for i, art in enumerate(articles[:5]):
            print(f"\n  [{i+1}] {art['title'][:60]}")
            print(f"      URL: {art['url'][:60]}...")
            print(f"      Published: {art['published']}")
            print(f"      Category: {art['category']}")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
