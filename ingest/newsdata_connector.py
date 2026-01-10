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
        API_KEY = config.get("newsdata", {}).get("api_key")
except Exception as e:
    API_KEY = None

class NewsDataConnector(pw.io.python.ConnectorSubject):
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
                                "created_utc": str(article.get("pubDate", "")),
                                "reliability": "High" 
                            }
                    if count > 0:
                        print(f"📰 NewsData: Fetched {count} new articles")
                else:
                    print(f"❌ NewsData Error {resp.status_code}: {resp.text[:100]}")
                    
            except Exception as e:
                print(f"❌ NewsData Connection Error: {e}")
                
            time.sleep(900)

class NewsSchema(pw.Schema):
    source: str
    text: str
    url: str
    created_utc: str
    reliability: str

newsdata_table = pw.io.python.read(
    NewsDataConnector(),
    schema=NewsSchema
)
