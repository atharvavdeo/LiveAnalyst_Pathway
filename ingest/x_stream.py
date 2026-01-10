# X (Twitter) streaming data source with rate limiting

import os
import time
import threading
import requests
from requests_oauthlib import OAuth1
import pathway as pw
from dotenv import load_dotenv

load_dotenv()

_request_lock = threading.Lock()
_last_request_time = 0
MIN_REQUEST_INTERVAL = 60
DAILY_REQUEST_LIMIT = 100
_daily_request_count = 0
_day_start = time.time()

def _rate_limit_check():
    global _last_request_time, _daily_request_count, _day_start
    
    if time.time() - _day_start > 86400:
        _daily_request_count = 0
        _day_start = time.time()
    
    if _daily_request_count >= DAILY_REQUEST_LIMIT:
        print(f"⚠️ Daily X API limit reached ({DAILY_REQUEST_LIMIT}). Waiting until reset...")
        return False
    
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        wait_time = MIN_REQUEST_INTERVAL - elapsed
        print(f"⏳ Rate limiting: waiting {wait_time:.0f}s before next X request...")
        time.sleep(wait_time)
    
    return True

def x_stream():
    global _last_request_time, _daily_request_count
    
    consumer_key = os.getenv("X_CONSUMER_KEY")
    consumer_secret = os.getenv("X_CONSUMER_SECRET")

    if not consumer_key or consumer_key == "your_x_consumer_key":
        print("⚠️ No X Keys. Streaming dummy social posts...")
        while True:
            yield {
                "source": "x",
                "text": "Rumor: People are saying the AI policy will ban chatbots! #panic",
                "score": 10,
                "url": "http://x.com",
                "created_utc": time.time()
            }
            time.sleep(5)

    auth = OAuth1(consumer_key, consumer_secret)
    
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    seen = set()
    
    while True:
        with _request_lock:
            if not _rate_limit_check():
                time.sleep(300)
                continue
            
            try:
                params = {
                    "query": "technology OR AI OR tech news -is:retweet lang:en",
                    "max_results": 10,
                    "tweet.fields": "created_at,public_metrics"
                }
                
                print(f"🔄 Fetching X posts... (Daily requests: {_daily_request_count + 1}/{DAILY_REQUEST_LIMIT})")
                resp = requests.get(search_url, auth=auth, params=params, timeout=30)
                _last_request_time = time.time()
                _daily_request_count += 1
                
                if resp.status_code == 429:
                    print("⚠️ X Rate limit hit! Waiting 15 minutes...")
                    time.sleep(900)
                    continue
                elif resp.status_code == 401:
                    print("❌ X Auth failed. Check your API keys.")
                    while True:
                        yield {
                            "source": "x",
                            "text": "Demo: X authentication failed, showing sample data.",
                            "score": 0,
                            "url": "http://x.com",
                            "created_utc": time.time()
                        }
                        time.sleep(60)
                elif resp.status_code != 200:
                    print(f"⚠️ X API Error {resp.status_code}: {resp.text[:200]}")
                    time.sleep(120)
                    continue
                
                data = resp.json()
                tweets = data.get("data", [])
                
                for tweet in tweets:
                    tweet_id = tweet.get("id")
                    if tweet_id and tweet_id not in seen:
                        seen.add(tweet_id)
                        metrics = tweet.get("public_metrics", {})
                        yield {
                            "source": "x",
                            "text": tweet.get("text", ""),
                            "score": metrics.get("like_count", 0) + metrics.get("retweet_count", 0),
                            "url": f"https://x.com/i/status/{tweet_id}",
                            "created_utc": time.time()
                        }
                
                print(f"✅ Fetched {len(tweets)} tweets. Next fetch in {MIN_REQUEST_INTERVAL}s")
                        
            except requests.exceptions.Timeout:
                print("⚠️ X API timeout. Retrying in 60s...")
            except Exception as e:
                print(f"X API Error: {e}")
            
        time.sleep(MIN_REQUEST_INTERVAL)

x_table = pw.io.python.read(
    x_stream,
    schema={"source": str, "text": str, "score": int, "url": str, "created_utc": float}
)
