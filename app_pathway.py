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

# Connectors (Classes)
from ingest.newsdata_connector import NewsDataConnector
from ingest.gnews_connector import GNewsConnector
from ingest.reddit_stream import RedditConnector
from ingest.hackernews_stream import HackerNewsConnector

# AI Pipeline
from pipeline.gemini_rag import pathway_rag_query

# Data Store
data_store = {
    "items": deque(maxlen=200),
    "stats": {"news": 0, "social": 0}
}
data_lock = threading.Lock()

def run_connector(generator, source_name):
    print(f"📡 Starting stream: {source_name}")
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
    except Exception as e:
        print(f"❌ Error in {source_name} stream: {e}")

app = FastAPI(title="LiveSocialAnalyst Pro")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    print("==================================================")
    print("🚀 LiveSocialAnalyst - Multi-Source Architecture")
    print("==================================================")
    
    # Start connector threads using .run() method of the classes
    threading.Thread(target=run_connector, args=(NewsDataConnector().run(), "newsdata"), daemon=True).start()
    threading.Thread(target=run_connector, args=(GNewsConnector().run(), "gnews"), daemon=True).start()
    threading.Thread(target=run_connector, args=(HackerNewsConnector().run(), "hackernews"), daemon=True).start()
    
    # Reddit optional (commented out as requested)
    # threading.Thread(target=run_connector, args=(RedditConnector().run(), "reddit"), daemon=True).start()
    
    print("✅ All streams active")

@app.get("/")
def root():
    frontend = Path(__file__).parent / "frontend" / "index.html"
    return HTMLResponse(frontend.read_text())

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
def query_endpoint(req: QueryRequest):
    with data_lock:
        snapshot = list(data_store["items"])
    
    if not snapshot:
        return {"error": "No data collected yet. Please wait..."}
        
    return pathway_rag_query(snapshot, req.query)

@app.get("/data")
def get_data():
    with data_lock:
        return {
            "news": [i for i in data_store["items"] if i['source'] in ['newsdata', 'gnews']][-10:],
            "hackernews": [i for i in data_store["items"] if i['source'] not in ['newsdata', 'gnews']][-10:],
            "total_news": data_store["stats"]["news"],
            "total_hackernews": data_store["stats"]["social"]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
