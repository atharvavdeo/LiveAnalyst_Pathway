import time
import requests
import yaml
from pathlib import Path

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
try:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
        API_KEY = config.get("newsdata", {}).get("api_key")
except Exception as e:
    API_KEY = None

class NewsDataConnector:
    """Simple generator-based connector for NewsData.io"""
    
    def run(self):
        if not API_KEY or API_KEY == "your_newsdata_api_key":
            print("⚠️ No NewsData.io Key configured. Skipping...")
            while True:
                time.sleep(3600)
                yield None
                
        seen_urls = set()
        url = "https://newsdata.io/api/1/latest"
        
        while True:
            try:
                # BROADER SCOPE: Changed categories
                params = {
                    "apikey": API_KEY,
                    "language": "en",
                    "category": "top,politics,world,business,technology" 
                }
                resp = requests.get(url, params=params, timeout=30)
                
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    
                    count = 0
                    for article in results:
                        link = article.get("link")
                        if link and link not in seen_urls:
                            seen_urls.add(link)
                            count += 1
                            
                            yield {
                                "source": "newsdata",
                                "text": f"{article.get('title', '')}. {article.get('description', '')}",
                                "url": link,
                                "image_url": article.get("image_url"),
                                "created_utc": str(article.get("pubDate", "")),
                                "reliability": "High" 
                            }
                    if count > 0:
                        print(f"📰 NewsData: Fetched {count} new articles")
                else:
                    print(f"❌ NewsData Error {resp.status_code}: {resp.text[:100]}")
                    
            except Exception as e:
                print(f"❌ NewsData Connection Error: {e}")
                
            time.sleep(300)  # Poll every 5 minutes

# --- ON-DEMAND CATEGORY FETCH ---
def fetch_category(category: str) -> list:
    """
    Fetch news for a specific category on demand.
    """
    if not API_KEY or API_KEY == "your_newsdata_api_key":
        print("⚠️ No NewsData Key for category fetch.")
        return []

    print(f"📰 NewsData Category Fetch: '{category}'")
    url = "https://newsdata.io/api/1/latest"
    
    params = {
        "apikey": API_KEY,
        "language": "en",
        "category": category,
        "country": "us,gb,in,ca,au" # Broaden reach
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        items = []
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            
            for article in results:
                items.append({
                    "source": "newsdata_ondemand",
                    "text": f"{article.get('title', '')}. {article.get('description', '')}",
                    "url": article.get("link"),
                    "image_url": article.get("image_url"), # Capture image if available
                    "created_utc": str(article.get("pubDate", "")),
                    "reliability": "High",
                    "category": category
                })
            print(f"✅ Found {len(items)} articles for category '{category}'.")
            return items
        else:
            print(f"❌ NewsData Category Error {resp.status_code}: {resp.text[:100]}")
            return []
            
    except Exception as e:
        print(f"❌ NewsData Category Exception: {e}")
        return []
