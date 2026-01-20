import time
import requests
import yaml
# import pathway as pw
from pathlib import Path

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
try:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
        gnews_config = config.get("gnews", {})
        API_KEY = gnews_config.get("api_key")
        LANG = gnews_config.get("language", "en")
        COUNTRY = gnews_config.get("country", "us")
except Exception as e:
    API_KEY = None

class GNewsConnector:
    def run(self):
        if not API_KEY or API_KEY == "your_gnews_api_key":
            print("⚠️ No GNews Key configured. Skipping...")
            while True:
                time.sleep(3600)
                yield None
                
        seen_urls = set()
        base_url = "https://gnews.io/api/v4/top-headlines"
        
        while True:
            try:
                # BROADER SCOPE: Removed 'topic=technology'
                # Fetching General Top Headlines
                params = {
                    "token": API_KEY,
                    "lang": LANG,
                    "country": COUNTRY,
                    "max": 10
                    # No 'topic' param means "General"
                }
                resp = requests.get(base_url, params=params, timeout=30)
                
                if resp.status_code == 200:
                    data = resp.json()
                    articles = data.get("articles", [])
                    
                    count = 0
                    for article in articles:
                        url = article.get("url")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            count += 1
                            
                            pub_date = article.get("publishedAt")
                            if not pub_date:
                                # Fallback to strict ISO format for now
                                import datetime
                                pub_date = datetime.datetime.utcnow().isoformat() + "Z"
                                
                            yield {
                                "source": "gnews",
                                "text": f"{article.get('title', '')}. {article.get('description', '')}",
                                "url": url,
                                "created_utc": pub_date,
                                "reliability": "High"
                            }
                    if count > 0:
                        print(f"🌍 GNews: Fetched {count} articles")
                else:
                    print(f"❌ GNews Error {resp.status_code}: {resp.text[:100]}")
                    
            except Exception as e:
                print(f"❌ GNews Connection Error: {e}")
                
            time.sleep(600)

# class GNewsSchema(pw.Schema):
#     source: str
#     text: str
#     url: str
#     created_utc: str
#     reliability: str


# --- ON-DEMAND HISTORICAL SEARCH ---
def search_historical(query: str, days: int = 1000) -> list:
    """
    Perform an on-demand historical search for specific keywords.
    Uses the /search endpoint instead of /top-headlines.
    """
    if not API_KEY or API_KEY == "your_gnews_api_key":
        print("⚠️ No GNews Key for historical search.")
        return []
        
    print(f"🌍 GNews Historical Search: '{query}' (Last {days} days)")
    base_url = "https://gnews.io/api/v4/search"
    
    # Calculate 'from' date if needed, but GNews defaults to sorting by relevance/date
    # Max count 10 for speed
    params = {
        "token": API_KEY,
        "q": query,
        "lang": LANG,
        # "country": COUNTRY,  <-- REMOVED to allow global search (e.g. India/Russia news)
        "max": 10,
        "sortby": "relevance"
    }
    
    try:
        resp = requests.get(base_url, params=params, timeout=30)
        items = []
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get("articles", [])
            
            for article in articles:
                items.append({
                    "source": "gnews_historical",
                    "text": f"{article.get('title', '')}. {article.get('description', '')}",
                    "url": article.get("url"),
                    "created_utc": article.get("publishedAt", ""),
                    "reliability": "High"
                })
            print(f"✅ Found {len(items)} historical articles.")
            return items
        else:
            print(f"❌ GNews Search Error: {resp.text}")
            return []
    except Exception as e:
        print(f"❌ GNews Search Exception: {e}")
        return []
