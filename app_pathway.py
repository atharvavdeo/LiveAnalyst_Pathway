# Main Application - Multi-Source Pathway Pipeline

import threading
import time
from collections import deque
from pathlib import Path
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


# Connectors (Classes & Functions)
from ingest.newsdata_connector import fetch_category as fetch_category_newsdata
from ingest.gnews_connector import GNewsConnector, search_historical
from ingest.reddit_stream import RedditConnector
from ingest.hackernews_stream import HackerNewsConnector
from ingest.firecrawl_connector import FirecrawlConnector, scrape_targeted
from ingest.opml_loader import OPMLIngestor, DEFAULT_OPML_URLS

# ... 

# --- NEW ENDPOINT FOR DYNAMIC CATEGORIES ---




# ... (Previous imports match existing file structure)

# --- NEW ENDPOINT FOR DYNAMIC CATEGORIES ---



# AI Pipeline
from pipeline.gemini_rag import pathway_rag_query

# Data Persistence
from data.database import save_articles_batch, search_history

# Data Store
data_store = {
    "items": deque(maxlen=500),  # Increased for OPML volume
    "stats": {"news": 0, "social": 0, "opml": 0}
}
data_lock = threading.Lock()

def run_connector(generator, source_name):
    print(f"📡 Starting stream: {source_name}")
    batch_buffer = []
    last_save = time.time()
    
    # DISABLED: Vector store causes mutex lock issues with sentence_transformers
    # Vector indexing will happen during RAG query instead (lazy indexing)
    # from pipeline.vector_store import get_vector_store
    # vs = get_vector_store()
        
    try:
        for item in generator:
            if item:
                with data_lock:
                    if "reliability" not in item:
                        item["reliability"] = "Unknown"
                    
                    data_store["items"].append(item)
                    
                    if source_name in ['newsdata', 'gnews', 'newsapi']:
                        data_store["stats"]["news"] += 1
                    elif source_name == 'opml':
                        data_store["stats"]["opml"] += 1
                    else:
                        data_store["stats"]["social"] += 1
                
                # ========== VECTOR INDEXING DISABLED (CAUSES MUTEX LOCK) ==========
                # Indexing moved to RAG query time to avoid startup locks
                # ================================================================
                
                # Buffer for DB save (batch is OK for DB)
                batch_buffer.append(item)
                
                # Save to DB every 10 items or 30 seconds
                if len(batch_buffer) >= 10 or (time.time() - last_save > 30):
                    count = save_articles_batch(batch_buffer)
                    if count > 0:
                        print(f"💾 {source_name}: Saved {count} items to DB")
                    batch_buffer = []
                    last_save = time.time()
                    
    except Exception as e:
        print(f"❌ Error in {source_name} stream: {e}")

app = FastAPI(title="LiveSocialAnalyst Pro")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    print("==================================================")
    print("🚀 LiveSocialAnalyst - Hybrid Architecture (DB + Live)")
    print("==================================================")
    
    # Start connector threads
    # NewsData.io replaces rate-limited NewsAPI
    # NewsData.io replaces rate-limited NewsAPI -> DISABLED BY USER REQUEST
    # from ingest.newsdata_connector import NewsDataConnector
    # threading.Thread(target=run_connector, args=(NewsDataConnector().run(), "newsdata"), daemon=True).start()
    threading.Thread(target=run_connector, args=(GNewsConnector().run(), "gnews"), daemon=True).start()
    threading.Thread(target=run_connector, args=(HackerNewsConnector().run(), "hackernews"), daemon=True).start()
    threading.Thread(target=run_connector, args=(RedditConnector().run(), "reddit"), daemon=True).start()
    threading.Thread(target=run_connector, args=(FirecrawlConnector().run(), "firecrawl"), daemon=True).start()
    
    # 🚀 NUCLEAR OPTION: OPML Mass Ingestion (1800+ feeds) - High Frequency (10s)
    global global_opml
    global_opml = OPMLIngestor(DEFAULT_OPML_URLS, poll_frequency=10)
    threading.Thread(target=run_connector, args=(global_opml.run(), "opml"), daemon=True).start()
    
    print("✅ All streams active (NewsData.io + OPML + GNews + HackerNews)")

# --- NEW ENDPOINT FOR DYNAMIC CATEGORIES ---
class CategoryRequest(BaseModel):
    category: str

@app.post("/fetch_news")
def fetch_news_endpoint(req: CategoryRequest):
    print(f"📥 Fetching news for category: {req.category}")
    
    # 1. Fetch from NewsData.io (replacing rate-limited NewsAPI)
    # 1. Fetch from NewsData.io -> DISABLED
    items = [] # fetch_category_newsdata(req.category)
    
    # 2. Persist to DB for future use
    if items:
        saved_count = save_articles_batch(items)
        print(f"💾 Persisted {saved_count} items from category '{req.category}'")
        
        # 3. Also add to live data store so it appears in "feed" if needed
        with data_lock:
            for item in items:
                data_store["items"].append(item)
                data_store["stats"]["news"] += 1
                
    return {"items": items}



@app.get("/")
def root():
    landing = Path(__file__).parent / "frontend" / "landing.html"
    return HTMLResponse(landing.read_text())

@app.get("/app")
def dashboard():
    frontend = Path(__file__).parent / "frontend" / "index.html"
    return HTMLResponse(frontend.read_text())

class QueryRequest(BaseModel):
    query: str

@app.post("/refresh_opml")
def refresh_opml_endpoint():
    print("🔄 API: Manual OPML Refresh Requested")
    if 'global_opml' in globals() and global_opml:
        global_opml.manual_refresh()
        return {"status": "triggered"}
    return {"status": "error", "message": "OPML ingestor not active"}

@app.post("/query")
def query_endpoint(req: QueryRequest):
    print(f"🔎 Received Query: {req.query}")
    used_web_fallback = False
    
    # === STEP 0: TRIGGER OPML REFRESH for fresh real-time data ===
    print("⚡ Triggering OPML refresh for fresh data...")
    if 'global_opml' in globals() and global_opml:
        global_opml.manual_refresh()
    
    # Small delay to let OPML fetch some fresh items
    import time
    time.sleep(1.5)
    
    # === STEP 1: Get snapshot of live stream (PRIMARY SOURCE) ===
    with data_lock:
        live_snapshot = list(data_store["items"])
    print(f"📊 Live stream snapshot: {len(live_snapshot)} items")
    
    # === STEP 2: Separate OPML items (PRIORITY) from other items ===
    opml_items = [i for i in live_snapshot if i.get('source') == 'opml']
    other_items = [i for i in live_snapshot if i.get('source') != 'opml']
    print(f"📰 OPML items: {len(opml_items)} | Other items: {len(other_items)}")
    
    # === STEP 3: Pre-filter for relevance ===
    query_words = set(req.query.lower().split())
    
    # Filter OPML items for relevance
    relevant_opml = []
    for item in opml_items:
        text = (item.get('text', '') + ' ' + item.get('url', '')).lower()
        if any(word in text for word in query_words):
            relevant_opml.append(item)
    
    # Filter other items for relevance
    relevant_other = []
    for item in other_items:
        text = (item.get('text', '') + ' ' + item.get('url', '')).lower()
        if any(word in text for word in query_words):
            relevant_other.append(item)
    
    print(f"🎯 Relevant OPML: {len(relevant_opml)} | Relevant Other: {len(relevant_other)}")
    
    # === STEP 4: Get DB history (always available) ===
    db_history = search_history(req.query, limit=10)
    print(f"📚 DB History matches: {len(db_history)}")
    
    # === STEP 5: Determine if we need web fallback ===
    on_demand_items = []
    MIN_RELEVANT_THRESHOLD = 3
    
    total_relevant = len(relevant_opml) + len(relevant_other) + len(db_history)
    if total_relevant < MIN_RELEVANT_THRESHOLD and len(req.query) > 3:
        print("⚠️ Insufficient live data, triggering web fallback...")
        used_web_fallback = True
        
        # Trigger GNews Historical Search
        hist_news = search_historical(req.query, days=1000)
        
        # Trigger Firecrawl Targeted Scrape (BACKUP)
        web_results = scrape_targeted(req.query)
        
        on_demand_items = hist_news + web_results
        
        # Persist these new findings for future use!
        if on_demand_items:
            saved = save_articles_batch(on_demand_items)
            print(f"💾 Persisted {saved} new on-demand items")
    else:
        print("✅ Sufficient live data, skipping web fallback")

    # === STEP 6: Combine all contexts - OPML FIRST (PRIORITY) ===
    # NEW Priority Order: [Relevant OPML] > [All OPML] > [Relevant Other] > [On-Demand] > [DB History]
    full_context = relevant_opml + opml_items + relevant_other + on_demand_items + db_history
    
    # Deduplicate by URL
    seen_urls = set()
    unique_context = []
    for item in full_context:
        url = item.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_context.append(item)
    
    # Count OPML vs other for logging
    opml_count = sum(1 for i in unique_context if i.get('source') == 'opml')
    print(f"🧠 Processing {len(unique_context)} items for AI (OPML: {opml_count} prioritized)...")
    
    # === STEP 7: Run RAG ===
    result = pathway_rag_query(unique_context, req.query)
    
    # === STEP 8: Add metadata to response ===
    result["used_web_fallback"] = used_web_fallback
    result["live_matches"] = len(relevant_opml) + len(relevant_other)
    result["opml_used"] = opml_count
        
    return result

@app.get("/data")
def get_data():
    with data_lock:
        items = list(data_store["items"])
        
        from fastapi.responses import JSONResponse
        content = {
            "newsapi": [i for i in items if i['source'] == 'newsapi'][-20:],
            "gnews": [i for i in items if i['source'] == 'gnews'][-20:],
            "hackernews": [i for i in items if i['source'] == 'hackernews'][-20:],
            "reddit": [i for i in items if i['source'] == 'reddit'][-20:],
            "firecrawl": [i for i in items if i['source'] == 'firecrawl'][-20:],
            "opml": [i for i in items if i['source'] == 'opml'][-50:],
            "newsdata": [i for i in items if 'newsdata' in i['source']][-20:],
            "stats": data_store["stats"]
        }
        return JSONResponse(content=content, headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"})

# === SMART TOPIC FILTER ENDPOINT ===
class TopicFilterRequest(BaseModel):
    topic: str

@app.post("/filter_topic")
def filter_topic_endpoint(req: TopicFilterRequest):
    """
    Smart topic filtering: Gets ALL live data + DB history and filters by topic using keywords.
    Returns properly categorized news for the selected topic.
    """
    print(f"🎯 Smart Topic Filter: {req.topic}")
    
    topic = req.topic.lower()
    
    # Define topic keywords for smart matching
    TOPIC_KEYWORDS = {
        "technology": ["tech", "ai", "software", "google", "apple", "microsoft", "meta", "computer", "startup", "app", "digital", "internet", "cloud", "data", "cyber", "robot", "programming", "developer"],
        "politics": ["trump", "biden", "election", "congress", "senate", "government", "president", "minister", "parliament", "political", "policy", "vote", "law", "legislation", "democrat", "republican", "modi", "putin"],
        "business": ["market", "stock", "economy", "company", "ceo", "finance", "investment", "bank", "trade", "revenue", "profit", "merger", "acquisition", "startup", "ipo"],
        "sports": ["football", "soccer", "basketball", "cricket", "tennis", "nba", "nfl", "fifa", "match", "game", "player", "team", "championship", "olympics", "win", "score"],
        "entertainment": ["movie", "film", "music", "celebrity", "hollywood", "bollywood", "actor", "singer", "album", "concert", "netflix", "streaming", "show", "series"],
        "health": ["health", "medical", "doctor", "hospital", "disease", "vaccine", "covid", "mental", "fitness", "medicine", "treatment", "patient", "wellness"],
        "science": ["science", "research", "study", "nasa", "space", "discovery", "climate", "environment", "biology", "physics", "chemistry", "scientist"],
        "world": ["international", "global", "war", "conflict", "china", "russia", "ukraine", "india", "europe", "asia", "africa", "foreign", "diplomacy"]
    }
    
    keywords = TOPIC_KEYWORDS.get(topic, [topic])
    
    # 1. Get LIVE data from stream
    with data_lock:
        live_items = list(data_store["items"])
    
    # 2. Get DB history
    db_items = search_history(topic, limit=30)
    print(f"📚 DB found {len(db_items)} historical items for '{topic}'")
    
    # 3. Combine all sources
    all_items = live_items + db_items
    
    # 4. Smart filter by topic keywords
    matching_items = []
    for item in all_items:
        text = (str(item.get('text') or '') + ' ' + str(item.get('url') or '') + ' ' + str(item.get('category') or '')).lower()
        # Check if ANY topic keyword matches
        if any(kw in text for kw in keywords):
            matching_items.append(item)
    
    print(f"🎯 Matched {len(matching_items)} items for topic '{topic}'")
    
    # 5. Deduplicate by URL
    seen_urls = set()
    unique_items = []
    for item in matching_items:
        url = item.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_items.append(item)
    
    # 6. Sort by freshness
    from datetime import datetime, timezone
    def parse_date(item):
        try:
            d = item.get('created_utc', '')
            if isinstance(d, str):
                if 'T' in d:
                    # ISO format
                    dt = datetime.fromisoformat(d.replace('Z', '+00:00'))
                    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                else:
                    # Try parsing rudimentary strings or fail
                    return datetime.min.replace(tzinfo=timezone.utc)
            elif isinstance(d, (int, float)):
                return datetime.fromtimestamp(d, timezone.utc)
            elif isinstance(d, datetime):
                return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except:
            pass
        return datetime.min.replace(tzinfo=timezone.utc)
    
    unique_items.sort(key=parse_date, reverse=True)
    
    # 7. Separate by source type for organized response
    opml_items = [i for i in unique_items if i.get('source') == 'opml'][:15]
    gnews_items = [i for i in unique_items if i.get('source') == 'gnews'][:10]
    newsdata_items = [i for i in unique_items if 'newsdata' in i.get('source', '')][:10]
    hn_items = [i for i in unique_items if i.get('source') == 'hackernews'][:5]
    db_items_filtered = [i for i in unique_items if '_db' in i.get('source', '')][:10]
    
    print(f"📊 Results: OPML={len(opml_items)}, GNews={len(gnews_items)}, NewsData={len(newsdata_items)}, HN={len(hn_items)}, DB={len(db_items_filtered)}")
    
    return {
        "topic": topic,
        "opml": opml_items,
        "gnews": gnews_items,
        "newsdata": newsdata_items,
        "hackernews": hn_items,
        "db_history": db_items_filtered,
        "total": len(unique_items)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
