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
        API_KEY = config.get("firecrawl", {}).get("api_key")
except Exception as e:
    API_KEY = None

class FirecrawlConnector(pw.io.python.ConnectorSubject):
    def run(self):
        if not API_KEY:
            print("⚠️ No Firecrawl Key configured. Skipping...")
            while True:
                time.sleep(3600)
                yield None
                
        seen_urls = set()
        
        # We will cycle through major topics
        topics = ["latest world news", "global politics", "major technology breakthroughs"]
        topic_idx = 0
        
        while True:
            try:
                # Firecrawl Search Endpoint
                url = "https://api.firecrawl.dev/v0/search"
                headers = {"Authorization": f"Bearer {API_KEY}"}
                payload = {
                    "query": topics[topic_idx],
                    "limit": 5,
                    "lang": "en",
                    "scrapeOptions": {"formats": ["markdown"]} 
                }
                
                resp = requests.post(url, headers=headers, json=payload, timeout=60)
                
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("data", [])
                    
                    count = 0
                    for item in results:
                        link = item.get("url")
                        if link and link not in seen_urls:
                            seen_urls.add(link)
                            count += 1
                            
                            # Extract snippet
                            markdown = item.get("markdown", "")
                            snippet = markdown[:500].replace("\n", " ").strip()
                            title = item.get("title", "News Update")
                            
                            yield {
                                "source": "firecrawl",
                                "text": f"{title}: {snippet}",
                                "url": link,
                                "created_utc": str(time.time()),
                                "reliability": "High"
                            }
                    
                    if count > 0:
                        print(f"🔥 Firecrawl: Found {count} items for '{topics[topic_idx]}'")
                else:
                    print(f"❌ Firecrawl Error {resp.status_code}: {resp.text[:100]}")
                    
            except Exception as e:
                print(f"❌ Firecrawl Connection Error: {e}")
            
            # Rotate topic
            topic_idx = (topic_idx + 1) % len(topics)
            
            # Poll every 5 minutes
            time.sleep(300)

class FirecrawlSchema(pw.Schema):
    source: str
    text: str
    url: str
    created_utc: str
    reliability: str


# --- ON-DEMAND TARGETED SCRAPING ---
def scrape_targeted(query: str) -> list:
    """
    Perform an active web scrape for a specific user query.
    """
    if not API_KEY:
        print("⚠️ No Firecrawl Key for targeted scrape.")
        return []
        
    print(f"🔥 Firecrawl Targeted Scrape: '{query}'")
    url = "https://api.firecrawl.dev/v0/search"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    payload = {
        "query": query,
        "limit": 3,  # Keep it small for speed
        "lang": "en",
        "scrapeOptions": {"formats": ["markdown"]} 
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=45)
        items = []
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("data", [])
            
            for item in results:
                markdown = item.get("markdown", "")
                snippet = markdown[:800].replace("\n", " ").strip() # Longer snippet for targeted
                title = item.get("title", "Web Result")
                
                items.append({
                    "source": "firecrawl_targeted",
                    "text": f"{title}: {snippet}",
                    "url": item.get("url"),
                    "created_utc": str(time.time()),
                    "reliability": "Medium"
                })
            print(f"✅ Found {len(items)} web results.")
            return items
        else:
            print(f"❌ Firecrawl Scrape Error: {resp.text}")
            return []
            
    except Exception as e:
        print(f"❌ Firecrawl Scrape Exception: {e}")
        return []
