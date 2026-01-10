# NewsData.io streaming data source

import os
import time
import requests
import pathway as pw
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("NEWSDATA_API_KEY")

def news_stream():
    if not API_KEY or API_KEY == "your_newsdata_key_here":
        print("⚠️ No NewsData.io Key found. Streaming dummy data...")
        while True:
            yield {
                "source": "news",
                "text": "Official News: The government has announced a new policy on AI usage.",
                "url": "http://newsdata.io",
                "created_utc": str(time.time())
            }
            time.sleep(10)
    
    seen = set()
    url = "https://newsdata.io/api/1/latest"
    while True:
        try:
            resp = requests.get(url, params={"apikey": API_KEY, "language": "en", "category": "technology"})
            data = resp.json()
            for article in data.get("results", []):
                article_url = article.get("link", "")
                if article_url and article_url not in seen:
                    seen.add(article_url)
                    yield {
                        "source": "news",
                        "text": f"{article.get('title', '')}. {article.get('description', '')}",
                        "url": article_url,
                        "created_utc": str(article.get("pubDate", ""))
                    }
        except Exception as e:
            print(f"NewsData.io Error: {e}")
        time.sleep(60)

news_table = pw.io.python.read(
    news_stream,
    schema={"source": str, "text": str, "url": str, "created_utc": str}
)
