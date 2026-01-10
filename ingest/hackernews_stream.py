"""
HackerNews Stream for Pathway
Real-time ingestion of HackerNews top stories using Pathway's streaming framework.
"""

import time
import requests
import pathway as pw

def hackernews_stream():
    """
    Generator that yields HackerNews stories for Pathway ingestion.
    Uses the free HackerNews Firebase API (no authentication required).
    """
    seen = set()
    
    while True:
        try:
            # Get top story IDs
            top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            resp = requests.get(top_url, timeout=10)
            story_ids = resp.json()[:20]  # Get top 20 stories
            
            for story_id in story_ids:
                if story_id in seen:
                    continue
                    
                # Fetch individual story
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                item_resp = requests.get(item_url, timeout=5)
                item = item_resp.json()
                
                if item and item.get("title"):
                    seen.add(story_id)
                    
                    text = item.get("title", "")
                    if item.get("text"):
                        text += f" - {item.get('text')[:200]}"
                    
                    yield {
                        "source": "hackernews",
                        "text": text,
                        "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        "created_utc": str(item.get("time", time.time())),
                        "score": item.get("score", 0)
                    }
            
            print(f"✅ HackerNews: Fetched {len(story_ids)} stories")
            
        except requests.exceptions.Timeout:
            print("⚠️ HackerNews timeout, retrying...")
        except Exception as e:
            print(f"❌ HackerNews error: {e}")
        
        # Poll every 2 minutes
        time.sleep(120)

# Create the Pathway Table for HackerNews
hackernews_table = pw.io.python.read(
    hackernews_stream,
    schema={"source": str, "text": str, "url": str, "created_utc": str, "score": int}
)
