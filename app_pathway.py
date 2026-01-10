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
from ingest.newsdata_connector import NewsDataConnector
from ingest.gnews_connector import GNewsConnector, search_historical
from ingest.reddit_stream import RedditConnector
from ingest.hackernews_stream import HackerNewsConnector
from ingest.firecrawl_connector import FirecrawlConnector, scrape_targeted

# AI Pipeline
from pipeline.gemini_rag import pathway_rag_query

# Data Persistence
from data.database import save_articles_batch, search_history

# Data Store
data_store = {
    "items": deque(maxlen=200),
    "stats": {"news": 0, "social": 0}
}
data_lock = threading.Lock()

def run_connector(generator, source_name):
    print(f"📡 Starting stream: {source_name}")
    batch_buffer = []
    last_save = time.time()
        
    try:
        for item in generator:
            if item:
                with data_lock:
                    if "reliability" not in item:
                        item["reliability"] = "Unknown"
                    
                    data_store["items"].append(item)
                    
                    if source_name in ['newsdata', 'gnews']:
                        data_store["stats"]["news"] += 1
                    else:
                        data_store["stats"]["social"] += 1
                
                # Buffer for DB save
                batch_buffer.append(item)
                
                # Save every 10 items or 30 seconds
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
    threading.Thread(target=run_connector, args=(NewsDataConnector().run(), "newsdata"), daemon=True).start()
    threading.Thread(target=run_connector, args=(GNewsConnector().run(), "gnews"), daemon=True).start()
    threading.Thread(target=run_connector, args=(HackerNewsConnector().run(), "hackernews"), daemon=True).start()
    threading.Thread(target=run_connector, args=(RedditConnector().run(), "reddit"), daemon=True).start()
    threading.Thread(target=run_connector, args=(FirecrawlConnector().run(), "firecrawl"), daemon=True).start()
    
    print("✅ All streams active")

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

@app.post("/query")
def query_endpoint(req: QueryRequest):
    print(f"🔎 Received Query: {req.query}")
    
    # 1. Get snapshot of live live stream (Fastest)
    with data_lock:
        live_snapshot = list(data_store["items"])
    
    # 2. Search History from DB (Local Persisted)
    db_history = search_history(req.query, limit=10)
    print(f"📚 DB History matches: {len(db_history)}")
    
    # 3. On-Demand Fetch (Slower, but targeted)
    #    Run specific search for user query if it's substantial
    on_demand_items = []
    if len(req.query) > 3:
        # Trigger GNews Historical Search
        hist_news = search_historical(req.query, days=1000)
        
        # Trigger Firecrawl Targeted Scrape
        web_results = scrape_targeted(req.query)
        
        on_demand_items = hist_news + web_results
        
        # Persist these new findings for future use!
        if on_demand_items:
            saved = save_articles_batch(on_demand_items)
            print(f"💾 Persisted {saved} new on-demand items")

    # 4. Combine all contexts
    #    Structure: [Fresh Live Stream] + [On-Demand Targeted] + [Historical DB]
    full_context = live_snapshot + on_demand_items + db_history
    
    # Deduplicate by URL
    seen_urls = set()
    unique_context = []
    for item in full_context:
        url = item.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_context.append(item)
    
    print(f"🧠 Processing {len(unique_context)} items for AI...")
        
    return pathway_rag_query(unique_context, req.query)

@app.get("/data")
def get_data():
    with data_lock:
        items = list(data_store["items"])
        
        return {
            "newsdata": [i for i in items if i['source'] == 'newsdata'][-20:],
            "gnews": [i for i in items if i['source'] == 'gnews'][-20:],
            "hackernews": [i for i in items if i['source'] == 'hackernews'][-20:],
            "reddit": [i for i in items if i['source'] == 'reddit'][-20:],
            "firecrawl": [i for i in items if i['source'] == 'firecrawl'][-20:],
            "stats": data_store["stats"]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
