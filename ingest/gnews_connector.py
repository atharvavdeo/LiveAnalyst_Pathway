import time
import requests
import yaml
import pathway as pw
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

class GNewsConnector(pw.io.python.ConnectorSubject):
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
                params = {
                    "token": API_KEY,
                    "lang": LANG,
                    "country": COUNTRY,
                    "topic": "technology",
                    "max": 10
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
                            
                            yield {
                                "source": "gnews",
                                "text": f"{article.get('title', '')}. {article.get('description', '')}",
                                "url": url,
                                "created_utc": article.get("publishedAt", ""),
                                "reliability": "High"
                            }
                    if count > 0:
                        print(f"🌍 GNews: Fetched {count} articles")
                else:
                    print(f"❌ GNews Error {resp.status_code}: {resp.text[:100]}")
                    
            except Exception as e:
                print(f"❌ GNews Connection Error: {e}")
                
            time.sleep(600)

class GNewsSchema(pw.Schema):
    source: str
    text: str
    url: str
    created_utc: str
    reliability: str

gnews_table = pw.io.python.read(
    GNewsConnector(),
    schema=GNewsSchema
)
