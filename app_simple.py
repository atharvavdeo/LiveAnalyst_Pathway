"""
LiveSocialAnalyst - Real-time News & Social Media Analysis with Reliability Scoring
A FastAPI-based application that aggregates news and social media, 
assigns reliability scores, and answers questions using OpenAI.
"""

import os
import time
import threading
from datetime import datetime
from typing import Optional
from collections import deque
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import openai

load_dotenv()

# ============== Configuration ==============
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# ============== Data Storage ==============
# Store recent items (max 100 each)
news_items = deque(maxlen=100)
hackernews_items = deque(maxlen=100)
data_lock = threading.Lock()

# ============== Reliability Scoring ==============
def get_reliability(source: str) -> dict:
    if source == "news":
        return {"score": "High", "label": "Official News Source", "warning": None}
    elif source == "hackernews":
        return {"score": "Medium", "label": "Tech Community Discussion", "warning": "⚠️ Community-sourced content. May contain opinions."}
    return {"score": "Unknown", "label": "Unknown Source", "warning": "Source reliability unknown."}

# ============== News Fetcher ==============
def fetch_news():
    """Fetch news from NewsData.io"""
    if not NEWSDATA_API_KEY or NEWSDATA_API_KEY == "your_newsdata_key_here":
        # Return dummy data
        return [{
            "source": "news",
            "text": "Official News: The government has announced a new policy on AI usage and regulation.",
            "url": "http://newsdata.io",
            "timestamp": datetime.now().isoformat(),
            "reliability": get_reliability("news")
        }]
    
    try:
        url = "https://newsdata.io/api/1/latest"
        params = {"apikey": NEWSDATA_API_KEY, "language": "en", "category": "technology"}
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        
        results = []
        for article in data.get("results", [])[:10]:
            results.append({
                "source": "news",
                "text": f"{article.get('title', '')}. {article.get('description', '')}",
                "url": article.get("link", ""),
                "timestamp": article.get("pubDate", datetime.now().isoformat()),
                "reliability": get_reliability("news")
            })
        return results
    except Exception as e:
        print(f"❌ NewsData.io Error: {e}")
        return []

# ============== Hacker News Fetcher (FREE, NO AUTH!) ==============
def fetch_hackernews():
    """Fetch top stories from Hacker News - completely free API"""
    try:
        # Get top story IDs
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        resp = requests.get(top_url, timeout=10)
        story_ids = resp.json()[:15]  # Get top 15 stories
        
        results = []
        for story_id in story_ids:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            item_resp = requests.get(item_url, timeout=5)
            item = item_resp.json()
            
            if item and item.get("title"):
                results.append({
                    "source": "hackernews",
                    "text": f"{item.get('title', '')}. {item.get('text', '') or ''}",
                    "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                    "timestamp": datetime.fromtimestamp(item.get("time", time.time())).isoformat(),
                    "score": item.get("score", 0),
                    "comments": item.get("descendants", 0),
                    "reliability": get_reliability("hackernews")
                })
        
        print(f"✅ Fetched {len(results)} Hacker News stories")
        return results
    except Exception as e:
        print(f"❌ Hacker News Error: {e}")
        return []

# ============== Background Data Fetcher ==============
def background_fetcher():
    """Background thread to periodically fetch data"""
    while True:
        try:
            # Fetch news every 5 minutes
            new_news = fetch_news()
            with data_lock:
                for item in new_news:
                    news_items.append(item)
            print(f"📰 Updated news: {len(new_news)} items")
            
            # Fetch Hacker News (free, no rate limits!)
            new_hn = fetch_hackernews()
            with data_lock:
                for item in new_hn:
                    hackernews_items.append(item)
            print(f"🔶 Updated Hacker News: {len(new_hn)} items")
            
        except Exception as e:
            print(f"❌ Background fetcher error: {e}")
        
        time.sleep(120)  # Check every 2 minutes

# ============== RAG Query with OpenAI/Groq ==============
def query_with_groq(system_prompt: str, user_prompt: str) -> str:
    """Fallback to Groq API (free tier)"""
    if not GROQ_API_KEY:
        raise Exception("No Groq API key configured. Please add GROQ_API_KEY to .env or add credits to OpenAI.")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=60
    )
    
    if resp.status_code != 200:
        raise Exception(f"Groq API error: {resp.text}")
    
    result = resp.json()
    return result["choices"][0]["message"]["content"]

def query_with_context(question: str) -> dict:
    """Answer question using collected context with reliability awareness"""
    
    with data_lock:
        all_items = list(news_items) + list(hackernews_items)
    
    if not all_items:
        # Fetch fresh data if empty
        all_items = fetch_news() + fetch_hackernews()
    
    # Build context string with reliability info
    context_parts = []
    for item in all_items[-20:]:  # Use last 20 items
        reliability = item.get("reliability", {})
        context_parts.append(
            f"[Source: {item['source'].upper()} | Reliability: {reliability.get('score', 'Unknown')}]\n"
            f"{item['text']}\n"
            f"URL: {item.get('url', 'N/A')}"
        )
    
    context = "\n\n---\n\n".join(context_parts)
    
    system_prompt = """You are a Real-Time News Analyst with access to live data from multiple sources.

CRITICAL RULES:
1. ALWAYS state the reliability level of information you cite
2. For "news" sources: Mark as "✅ VERIFIED (Official News)"  
3. For "hackernews" sources: Mark as "🔶 COMMUNITY (Hacker News)" - tech community discussions
4. If mixing sources, clearly distinguish which facts come from which
5. Be concise but thorough
6. If you don't have relevant information, say so

Format your response with clear reliability indicators."""

    user_prompt = f"""Based on the following real-time data, answer this question: {question}

CONTEXT DATA:
{context}

Remember to indicate the reliability of each piece of information you use."""

    # Count sources
    news_count = sum(1 for i in all_items[-20:] if i["source"] == "news")
    hn_count = sum(1 for i in all_items[-20:] if i["source"] == "hackernews")
    sources_info = {
        "news": news_count,
        "hackernews": hn_count,
        "total": len(all_items[-20:])
    }

    # Try OpenAI first
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        return {"answer": answer, "sources_analyzed": sources_info}
        
    except Exception as openai_error:
        print(f"⚠️ OpenAI failed: {openai_error}")
        
        # Try Groq as fallback
        try:
            print("🔄 Falling back to Groq...")
            answer = query_with_groq(system_prompt, user_prompt)
            return {"answer": answer + "\n\n_[Powered by Groq]_", "sources_analyzed": sources_info}
        except Exception as groq_error:
            error_msg = f"OpenAI: {str(openai_error)[:100]}... | Groq: {str(groq_error)[:100]}"
            return {
                "error": error_msg, 
                "answer": f"⚠️ API Error - Your OpenAI quota is exceeded and Groq is not configured.\n\nTo fix this:\n1. Add credits at https://platform.openai.com/account/billing\n2. OR get a free Groq API key at https://console.groq.com/keys and add GROQ_API_KEY to your .env file", 
                "sources_analyzed": sources_info
            }

# ============== FastAPI App ==============
app = FastAPI(
    title="LiveSocialAnalyst",
    description="Real-time News & Social Media Analysis with Reliability Scoring",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: Optional[str]
    sources_analyzed: Optional[dict]
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Start background data fetcher on app startup"""
    print("🚀 Starting LiveSocialAnalyst...")
    print(f"   OpenAI API: {'✅ Configured' if OPENAI_API_KEY else '❌ Missing'}")
    print(f"   NewsData.io: {'✅ Configured' if NEWSDATA_API_KEY else '⚠️ Demo Mode'}")
    print(f"   Hacker News: ✅ Free API (No auth needed)")
    
    # Start background fetcher
    fetcher_thread = threading.Thread(target=background_fetcher, daemon=True)
    fetcher_thread.start()
    print("📡 Background data fetcher started")

@app.get("/")
async def root():
    """Serve the frontend dashboard"""
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if frontend_path.exists():
        return HTMLResponse(content=frontend_path.read_text(), status_code=200)
    return {
        "message": "LiveSocialAnalyst API",
        "endpoints": {
            "POST /query": "Ask a question about current news/social media",
            "GET /status": "Check system status and rate limits",
            "GET /data": "View collected data"
        }
    }

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Ask a question and get an answer with reliability-aware context"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    result = query_with_context(request.query)
    return result

@app.post("/")
async def query_root(request: QueryRequest):
    """Alternative endpoint for queries at root"""
    return await query(request)

@app.get("/status")
async def status():
    """Get system status"""
    with data_lock:
        news_count = len(news_items)
        hn_count = len(hackernews_items)
    
    return {
        "status": "running",
        "data_collected": {
            "news_items": news_count,
            "hackernews_items": hn_count
        },
        "api_status": {
            "openai": "configured" if OPENAI_API_KEY else "missing",
            "newsdata": "configured" if NEWSDATA_API_KEY else "demo_mode",
            "hackernews": "active"
        }
    }

@app.get("/data")
async def get_data():
    """View collected data"""
    with data_lock:
        return {
            "news": list(news_items)[-10:],
            "hackernews": list(hackernews_items)[-10:],
            "total_news": len(news_items),
            "total_hackernews": len(hackernews_items)
        }

# ============== Main ==============
if __name__ == "__main__":
    import uvicorn
    print("🚀 Live Analyst running at http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
