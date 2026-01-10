import os
import time
import pathway as pw
import praw
from dotenv import load_dotenv

load_dotenv()

def reddit_stream():
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")

    # Mock data if no keys provided (SAFE MODE for Demo)
    if not client_id or client_id == "your_reddit_id":
        print("⚠️ No Reddit Keys. Streaming dummy social posts...")
        while True:
            yield {
                "source": "reddit",
                "text": "Rumor: People are saying the AI policy will ban chatbots! #panic",
                "score": 10,
                "url": "http://reddit.com",
                "created_utc": time.time()
            }
            time.sleep(5)

    # Real Reddit Stream
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent="live-social-analyst:v1.0"
    )
    subreddit = reddit.subreddit("technology+worldnews")
    try:
        for submission in subreddit.stream.submissions(skip_existing=True):
            yield {
                "source": "reddit",
                "text": f"{submission.title} {submission.selftext}",
                "score": submission.score,
                "url": submission.url,
                "created_utc": submission.created_utc
            }
    except Exception as e:
        print(f"Reddit Error: {e}")

reddit_table = pw.io.python.read(
    reddit_stream,
    schema={"source": str, "text": str, "score": int, "url": str, "created_utc": float}
)
