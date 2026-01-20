#!/usr/bin/env python3
"""
SIMPLE BACKEND TEST - Tests OPML fetching with minimal dependencies
This isolates the OPML functionality without vector stores or heavy imports
"""

import threading
import time
from collections import deque
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import ONLY the OPML loader
from ingest.opml_loader import OPMLIngestor, DEFAULT_OPML_URLS

# Simple Data Store
data_store = {
    "items": deque(maxlen=500),
    "stats": {"opml": 0}
}
data_lock = threading.Lock()

def run_opml_stream(generator):
    print("📡 Starting OPML stream...")
    try:
        for item in generator:
            if item:
                with data_lock:
                    data_store["items"].append(item)
                    data_store["stats"]["opml"] += 1
                    
                    # Log progress
                    if data_store["stats"]["opml"] % 10 == 0:
                        print(f"📰 OPML: {data_store['stats']['opml']} items collected")
    except Exception as e:
        print(f"❌ OPML Error: {e}")

app = FastAPI(title="Simple OPML Test")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    print("=" * 60)
    print("🧪 SIMPLE OPML BACKEND TEST")
    print("=" * 60)
    
    # Start ONLY the OPML stream
    global global_opml
    global_opml = OPMLIngestor(DEFAULT_OPML_URLS, poll_frequency=30)
    threading.Thread(target=run_opml_stream, args=(global_opml.run(),), daemon=True).start()
    
    print("✅ OPML stream started")

@app.get("/data")
def get_data():
    with data_lock:
        items = list(data_store["items"])
        
        return {
            "opml": items[-20:],  # Last 20 OPML items
            "total_count": len(items),
            "stats": data_store["stats"]
        }

@app.get("/test")
def test():
    return {"status": "OK", "timestamp": time.time()}

@app.post("/refresh_opml")
def refresh_opml():
    if 'global_opml' in globals() and global_opml:
        global_opml.manual_refresh()
        return {"status": "triggered"}
    return {"status": "error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
