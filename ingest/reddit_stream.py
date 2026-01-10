import yaml
import time
import pathway as pw
import praw
from pathlib import Path

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
reddit_config = {}
try:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
        reddit_config = config.get("reddit", {})
except Exception:
    pass

class RedditConnector(pw.io.python.ConnectorSubject):
    def run(self):
        client_id = reddit_config.get("client_id")
        client_secret = reddit_config.get("client_secret")
        user_agent = reddit_config.get("user_agent", "LiveSocialAnalyst/0.1")

        if not client_id or client_id.startswith("your_") or client_id.startswith("YOUR_"):
            print("⚠️ Reddit credentials missing or placeholder. Streaming disabled.")
            while True:
                time.sleep(3600)
                yield None

        try:
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            print(f"🔌 Connected to Reddit as: {reddit.read_only_mode}")
            
            # BROADER SCOPE: Added worldnews, news, politics
            subreddit = reddit.subreddit("worldnews+news+politics+technology+openai+artificial")
            print("✅ Reddit Stream Active: Tracking World/News/Tech subreddits...")
            
            for submission in subreddit.stream.submissions(skip_existing=True):
                yield {
                    "source": "reddit",
                    "text": f"{submission.title} {submission.selftext[:500]}",
                    "score": submission.score,
                    "url": submission.url,
                    "created_utc": submission.created_utc,
                    "reliability": "Low"
                }
        except Exception as e:
            print(f"❌ Reddit Stream Error: {e}")
            time.sleep(30)

class RedditSchema(pw.Schema):
    source: str
    text: str
    score: int
    url: str
    created_utc: float
    reliability: str

reddit_table = pw.io.python.read(
    RedditConnector(),
    schema=RedditSchema
)
