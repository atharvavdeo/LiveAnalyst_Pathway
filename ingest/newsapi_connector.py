import time
import requests
import yaml
import pathway as pw
from pathlib import Path
from datetime import datetime

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
try:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
        API_KEY = config.get("newsapi", {}).get("api_key")
        COUNTRY = config.get("newsapi", {}).get("country", "us")
except Exception as e:
    API_KEY = None
    COUNTRY = "us"

class NewsApiConnector(pw.io.python.ConnectorSubject):
    def run(self):
        if not API_KEY:
            print("⚠️ No NewsAPI Key configured. Skipping stream...")
            while True:
                time.sleep(3600)
                yield None
                
        seen_urls = set()
        url = "https://newsapi.org/v2/top-headlines"
        
        while True:
            try:
                # Cycle through main categories for the general stream
                categories = ["business", "technology", "general"]
                
                for cat in categories:
                    params = {
                        "apiKey": API_KEY,
                        "country": COUNTRY,
                        "category": cat,
                        "pageSize": 5
                    }
                    resp = requests.get(url, params=params, timeout=10)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        articles = data.get("articles", [])
                        
                        for art in articles:
                            link = art.get("url")
                            if link and link not in seen_urls:
                                seen_urls.add(link)
                                yield {
                                    "source": "newsapi",
                                    "text": f"{art.get('title')}",
                                    "url": link,
                                    "image_url": art.get("urlToImage"),
                                    "created_utc": art.get("publishedAt"),
                                    "reliability": "High",
                                    "category": cat
                                }
                    time.sleep(2) # Be gentle with rate limits
                    
            except Exception as e:
                print(f"❌ NewsAPI Connection Error: {e}")
                
            time.sleep(900) # Poll every 15 mins

class NewsSchema(pw.Schema):
    source: str
    text: str
    url: str
    created_utc: str
    reliability: str
    category: str

newsapi_table = pw.io.python.read(
    NewsApiConnector(),
    schema=NewsSchema
)

# --- ON-DEMAND CATEGORY FETCH ---
def fetch_category_newsapi(category: str) -> list:
    """
    Fetch news for a specific category on demand using NewsAPI.
    """
    if not API_KEY:
        print("⚠️ No NewsAPI Key for category fetch.")
        return []

    print(f"📰 NewsAPI Fetch: '{category}'")
    url = "https://newsapi.org/v2/top-headlines"
    
    # Defaults
    params = {
        "apiKey": API_KEY,
        "country": COUNTRY,
        "pageSize": 20
    }
    
    cat_lower = category.lower()
    
    # 1. Standard NewsAPI Categories
    valid_cats = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
    
    if cat_lower in valid_cats:
        params["category"] = cat_lower
        
    # 2. Mappings & Keywords
    elif cat_lower == "world":
        params["category"] = "general"
        
    elif cat_lower == "politics":
        params["category"] = "general"
        params["q"] = "politics" # Keyword filter
        
    elif cat_lower == "environment" or cat_lower == "planet":
        params["category"] = "science"
        params["q"] = "climate OR environment"
        
    elif cat_lower == "food":
        params["category"] = "health"
        params["q"] = "food OR nutrition"
        
    elif cat_lower == "cinema":
        params["category"] = "entertainment"
        params["q"] = "movie OR film"
        
    elif cat_lower == "cinema":
        params["category"] = "entertainment"
        params["q"] = "movie OR film"
        
    elif cat_lower == "fun":
        # SPECIAL CASE: 'fun' needs broad search, 'top-headlines' is too strict
        print("🎉 Fetching FUN stream via Everything endpoint...")
        items = search_newsapi("weird news OR viral OR funny OR space OR pop culture")
        
        # INJECT USER BLOG (Requested Feature)
        user_blog = {
            "source": "Atharva's Blog",
            "text": "Raw and uncompiled goodsh**. A personal corner on the internet where I explore tech, ideas, art and everything in between — one experiment, one mistake, and one honest thought at a time.",
            "url": "https://blogposts.framer.wiki",
            "image_url": "https://framerusercontent.com/images/k7aX5y2y3q4z.jpg", # Placeholder/Framer vibe
            "created_utc": "2025-01-01T00:00:00Z",
            "reliability": "Personal",
            "category": "featured"
        }
        # Prepend to list
        items.insert(0, user_blog)
        
        # FILTER OUT UNWANTED ARTIFACTS (User Request)
        items = [i for i in items if "Senior Internet Typist" not in i['text']]
        
        return items
        
    else:
        # Fallback for unknown
        params["category"] = "general"
        params["q"] = category
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        items = []
        
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get("articles", [])
            
            for art in articles:
                items.append({
                    "source": "newsapi_ondemand",
                    "text": art.get('title'),
                    "url": art.get("url"),
                    "image_url": art.get("urlToImage"), 
                    "created_utc": art.get("publishedAt"),
                    "reliability": "High",
                    "category": category
                })
            print(f"✅ Found {len(items)} articles for category '{category}'.")
            return items
        else:
            print(f"❌ NewsAPI Error {resp.status_code}: {resp.json().get('message')}")
            return []
            
    except Exception as e:
        print(f"❌ NewsAPI Exception: {e}")
        return []

# --- ON-DEMAND SEARCH FALLBACK ---
def search_newsapi(query: str) -> list:
    """
    Fallback search using NewsAPI 'everything' endpoint.
    Useful when GNews fails for broad topics.
    """
    if not API_KEY:
        return []
        
    print(f"📰 NewsAPI Search Fallback: '{query}'")
    url = "https://newsapi.org/v2/everything"
    
    params = {
        "apiKey": API_KEY,
        "q": query,
        "language": "en",
        "sortBy": "relevance",
        "pageSize": 10
    }
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        items = []
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get("articles", [])
            for art in articles:
                items.append({
                    "source": "newsapi_search",
                    "text": f"{art.get('title')}. {art.get('description', '')}",
                    "url": art.get("url"),
                    "image_url": art.get("urlToImage"), 
                    "created_utc": art.get("publishedAt"),
                    "reliability": "High",
                    "category": "search_result"
                })
            print(f"✅ NewsAPI found {len(items)} items for '{query}'")
            return items
        else:
            print(f"❌ NewsAPI Search Error: {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ NewsAPI Search Exception: {e}")
        return []
