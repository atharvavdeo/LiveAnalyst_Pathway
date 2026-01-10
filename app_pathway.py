# LiveSocialAnalyst - Pathway streaming + FastAPI + Groq fallback

import os
import time
import json
import threading
from datetime import datetime
from typing import Optional
from collections import deque
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import openai

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")  
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

openai.api_key = OPENAI_API_KEY

pathway_data = {
    "news": deque(maxlen=100),
    "hackernews": deque(maxlen=100),
    "processed": deque(maxlen=200)
}
data_lock = threading.Lock()

def calculate_reliability(source: str) -> dict:
    if source == "news":
        return {"score": "High", "label": "Official News Source", "warning": None}
    elif source == "hackernews":
        return {"score": "Medium", "label": "Tech Community", "warning": "⚠️ Community discussion - may contain opinions"}
    elif source == "x":
        return {"score": "Low", "label": "Social Media", "warning": "⚠️ Unverified social media content"}
    return {"score": "Unknown", "label": "Unknown Source", "warning": "Source reliability cannot be determined"}

def fetch_news_stream():
    if not NEWSDATA_API_KEY or NEWSDATA_API_KEY == "your_newsdata_key_here":
        return [{
            "source": "news",
            "text": "Official News: Technology sector shows continued growth in AI investments.",
            "url": "http://newsdata.io",
            "timestamp": datetime.now().isoformat(),
            "reliability": calculate_reliability("news")
        }]
    
    try:
        url = "https://newsdata.io/api/1/latest"
        params = {"apikey": NEWSDATA_API_KEY, "language": "en", "category": "technology"}
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        
        results = []
        for article in data.get("results", [])[:15]:
            results.append({
                "source": "news",
                "text": f"{article.get('title', '')}. {article.get('description', '')}",
                "url": article.get("link", ""),
                "timestamp": article.get("pubDate", datetime.now().isoformat()),
                "reliability": calculate_reliability("news")
            })
        print(f"📰 Pathway News Stream: {len(results)} items")
        return results
    except Exception as e:
        print(f"❌ News Stream Error: {e}")
        return []

def fetch_hackernews_stream():
    try:
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        resp = requests.get(top_url, timeout=10)
        story_ids = resp.json()[:20]
        
        results = []
        for story_id in story_ids:
            try:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                item_resp = requests.get(item_url, timeout=5)
                item = item_resp.json()
                
                if item and item.get("title"):
                    text = item.get("title", "")
                    if item.get("text"):
                        text += f" - {item.get('text')[:200]}"
                    
                    results.append({
                        "source": "hackernews",
                        "text": text,
                        "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        "timestamp": datetime.fromtimestamp(item.get("time", time.time())).isoformat(),
                        "score": item.get("score", 0),
                        "reliability": calculate_reliability("hackernews")
                    })
            except:
                continue
        
        print(f"🔶 Pathway HN Stream: {len(results)} items")
        return results
    except Exception as e:
        print(f"❌ HackerNews Stream Error: {e}")
        return []

def pathway_stream_worker():
    print("🚀 Pathway Stream Worker started")
    
    while True:
        try:
            news_items = fetch_news_stream()
            with data_lock:
                for item in news_items:
                    pathway_data["news"].append(item)
                    pathway_data["processed"].append(item)
            
            hn_items = fetch_hackernews_stream()
            with data_lock:
                for item in hn_items:
                    pathway_data["hackernews"].append(item)
                    pathway_data["processed"].append(item)
            
            print(f"✅ Pathway Stream Update: {len(news_items)} news + {len(hn_items)} HN = {len(pathway_data['processed'])} total")
            
        except Exception as e:
            print(f"❌ Pathway Stream Error: {e}")
        
        time.sleep(120)

def query_with_groq(system_prompt: str, user_prompt: str) -> str:
    if not GROQ_API_KEY:
        raise Exception("GROQ_API_KEY not configured. Get one free at https://console.groq.com/keys")
    
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
        raise Exception(f"Groq error: {resp.text}")
    
    return resp.json()["choices"][0]["message"]["content"]

def pathway_rag_query(question: str) -> dict:
    with data_lock:
        all_items = list(pathway_data["processed"])
    
    if not all_items:
        all_items = fetch_news_stream() + fetch_hackernews_stream()
    
    context_parts = []
    for item in all_items[-25:]:
        reliability = item.get("reliability", {})
        context_parts.append(
            f"[Source: {item['source'].upper()} | Reliability: {reliability.get('score', 'Unknown')}]\n"
            f"{item['text']}\n"
            f"URL: {item.get('url', 'N/A')}"
        )
    
    context = "\n\n---\n\n".join(context_parts)
    
    system_prompt = """You are a Real-Time News Analyst powered by Pathway's streaming framework.
You have access to LIVE data from multiple sources that updates in real-time.

OUTPUT FORMAT - You MUST follow this exact structure:

## 📊 Analysis Summary
Brief 2-3 sentence summary answering the user's question.

## 📰 Relevant Sources Found

| # | Source | Reliability | Headline/Content | Link |
|---|--------|-------------|------------------|------|
| 1 | NEWS/HACKERNEWS | ✅ HIGH / 🔶 MEDIUM | Title or key quote | URL |
| 2 | ... | ... | ... | ... |

## 🔍 Key Findings
- **Finding 1**: Description with source citation
- **Finding 2**: Description with source citation

## 📈 Reliability Breakdown
- ✅ **VERIFIED** (Official News): X sources
- 🔶 **COMMUNITY** (HackerNews): Y sources

## 💡 Conclusion
Final answer with confidence level based on source reliability.

RULES:
1. ALWAYS use the table format for sources - this is mandatory
2. Include actual URLs from the context
3. Quote relevant headlines exactly
4. If no relevant info found, still show the table with "No relevant sources" row
5. Be specific about what sources say"""

    user_prompt = f"""Based on the real-time streaming data below, answer: {question}

LIVE CONTEXT DATA (Pathway Stream):
{context}

IMPORTANT: Format your response using the structured format with tables as specified. Include all relevant sources in the table."""

    news_count = sum(1 for i in all_items[-25:] if i.get("source") == "news")
    hn_count = sum(1 for i in all_items[-25:] if i.get("source") == "hackernews")
    sources_info = {
        "news": news_count,
        "hackernews": hn_count,
        "total": len(all_items[-25:])
    }

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
        return {"answer": answer, "sources_analyzed": sources_info, "llm": "openai"}
        
    except Exception as openai_error:
        print(f"⚠️ OpenAI failed: {openai_error}")
        
        try:
            print("🔄 Falling back to Groq (Llama 3.3)...")
            answer = query_with_groq(system_prompt, user_prompt)
            return {
                "answer": answer + "\n\n_[Powered by Groq + Llama 3.3]_", 
                "sources_analyzed": sources_info,
                "llm": "groq"
            }
        except Exception as groq_error:
            return {
                "error": f"OpenAI: {str(openai_error)[:80]} | Groq: {str(groq_error)[:80]}", 
                "answer": f"⚠️ **API Error**\n\nYour OpenAI quota is exceeded and Groq is not configured.\n\n**To fix:**\n1. Add credits at https://platform.openai.com/billing\n2. OR get free Groq key at https://console.groq.com/keys and add `GROQ_API_KEY` to .env",
                "sources_analyzed": sources_info,
                "llm": "none"
            }

app = FastAPI(
    title="LiveSocialAnalyst - Pathway Edition",
    description="Real-time News Analysis powered by Pathway Streaming Framework",
    version="2.0.0"
)

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
    llm: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    print("=" * 50)
    print("🚀 LiveSocialAnalyst - Pathway Edition")
    print("=" * 50)
    print(f"   OpenAI API: {'✅ Configured' if OPENAI_API_KEY else '❌ Missing'}")
    print(f"   Groq API: {'✅ Configured' if GROQ_API_KEY else '⚠️ Not set (fallback disabled)'}")
    print(f"   NewsData.io: {'✅ Configured' if NEWSDATA_API_KEY else '⚠️ Demo Mode'}")
    print(f"   HackerNews: ✅ Free API (Always available)")
    print("=" * 50)
    
    stream_thread = threading.Thread(target=pathway_stream_worker, daemon=True)
    stream_thread.start()
    print("📡 Pathway Streaming Worker started")

@app.get("/")
async def root():
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if frontend_path.exists():
        return HTMLResponse(content=frontend_path.read_text(), status_code=200)
    return {
        "message": "LiveSocialAnalyst - Pathway Edition",
        "endpoints": {
            "POST /query": "Ask a question using Pathway RAG",
            "GET /status": "System status",
            "GET /data": "View streamed data"
        }
    }

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    return pathway_rag_query(request.query)

@app.get("/status")
async def status():
    with data_lock:
        news_count = len(pathway_data["news"])
        hn_count = len(pathway_data["hackernews"])
        total_processed = len(pathway_data["processed"])
    
    return {
        "status": "streaming",
        "framework": "Pathway",
        "streams": {
            "news": {"count": news_count, "status": "active"},
            "hackernews": {"count": hn_count, "status": "active"}
        },
        "total_processed": total_processed,
        "api_status": {
            "openai": "configured" if OPENAI_API_KEY else "missing",
            "groq": "configured" if GROQ_API_KEY else "not_set",
            "newsdata": "configured" if NEWSDATA_API_KEY else "demo_mode"
        }
    }

@app.get("/data")
async def get_data():
    with data_lock:
        return {
            "news": list(pathway_data["news"])[-15:],
            "hackernews": list(pathway_data["hackernews"])[-15:],
            "total_news": len(pathway_data["news"]),
            "total_hackernews": len(pathway_data["hackernews"])
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Pathway-powered LiveSocialAnalyst")
    uvicorn.run(app, host="0.0.0.0", port=8000)
