import tweepy
import time
import yaml
from pathlib import Path

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
try:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
        twitter_config = config.get("twitter", {})
        BEARER_TOKEN = twitter_config.get("bearer_token")
except Exception as e:
    BEARER_TOKEN = None

class TwitterConnector:
    def run(self):
        if not BEARER_TOKEN or "YOUR" in BEARER_TOKEN:
            print("⚠️ No Twitter Bearer Token configured. Skipping...")
            while True:
                time.sleep(3600)
                yield None
        
        print("🐦 Twitter: Initializing real-time stream...")
        
        # Initialize Twitter API v2 client
        client = tweepy.Client(bearer_token=BEARER_TOKEN)
        
        seen_tweets = set()
        
        # Keywords for tech/news trending topics
        query = "(breaking OR news OR tech OR AI OR latest) lang:en -is:retweet"
        
        while True:
            try:
                # Search recent tweets (last 30 seconds to 7 days)
                tweets = client.search_recent_tweets(
                    query=query,
                    max_results=10,
                    tweet_fields=['created_at', 'author_id', 'public_metrics']
                )
                
                if tweets.data:
                    count = 0
                    for tweet in tweets.data:
                        if tweet.id not in seen_tweets:
                            seen_tweets.add(tweet.id)
                            count += 1
                            
                            yield {
                                "source": "twitter",
                                "text": tweet.text,
                                "url": f"https://twitter.com/i/web/status/{tweet.id}",
                                "created_utc": tweet.created_at.isoformat(),
                                "reliability": "Medium"  # Unverified social content
                            }
                    
                    if count > 0:
                        print(f"🐦 Twitter: Fetched {count} real-time tweets")
                else:
                    print("🐦 Twitter: No new tweets")
                    
            except tweepy.errors.TooManyRequests:
                print("⏳ Twitter: Rate limited, waiting 15min...")
                time.sleep(900)
            except Exception as e:
                print(f"❌ Twitter Error: {e}")
                time.sleep(60)
            
            # Poll every 30 seconds for fresh tweets
            time.sleep(30)
