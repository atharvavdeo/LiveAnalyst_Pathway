# HackerNews streaming data source

import time
import requests
import pathway as pw

def hackernews_stream():
    seen = set()
    
    while True:
        try:
            top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            resp = requests.get(top_url, timeout=10)
            story_ids = resp.json()[:20]
            
            for story_id in story_ids:
                if story_id in seen:
                    continue
                    
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
        
        time.sleep(120)

hackernews_table = pw.io.python.read(
    hackernews_stream,
    schema={"source": str, "text": str, "url": str, "created_utc": str, "score": int}
)
