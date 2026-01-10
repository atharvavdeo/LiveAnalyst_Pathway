# Enhanced RAG Pipeline with Hybrid Vector + Live Search

import google.generativeai as genai
import yaml
from pathlib import Path
import os
import requests
import time

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
try:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
        GEMINI_API_KEY = config.get("gemini", {}).get("api_key")
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
except Exception as e:
    print(f"⚠️ Error loading config for Gemini: {e}")
    GEMINI_API_KEY = None

# Vector Store (lazy import to avoid startup delay)
_vector_store = None

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        try:
            from pipeline.vector_store import VectorStore
            _vector_store = VectorStore()
        except Exception as e:
            print(f"⚠️ Vector store unavailable: {e}")
            _vector_store = False  # Mark as failed
    return _vector_store if _vector_store else None


def filter_fresh_items(items: list, max_age_seconds: int = 300) -> list:
    """
    Filter items to only include those created within max_age_seconds.
    Default: 5 minutes (300 seconds)
    """
    if not items:
        return []
    
    current_time = time.time()
    fresh = []
    
    for item in items:
        created = item.get('created_utc', 0)
        
        # Handle ISO date strings (e.g., "2026-01-10T07:57:09Z")
        if isinstance(created, str):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                created = dt.timestamp()
            except:
                created = 0
        else:
            try:
                created = float(created)
            except (ValueError, TypeError):
                created = 0
        
        # Exempt on-demand/historical sources from freshness check
        source = item.get('source', '')
        category = item.get('category', '')
        if 'historical' in source or 'targeted' in source or 'newsapi_search' in source or category == 'search_result':
            fresh.append(item)
            continue
            
        age = current_time - created
        if age < max_age_seconds or created == 0:  # Include items without timestamp
            fresh.append(item)
    
    return fresh


def filter_relevant_items(items: list, query: str) -> list:
    """
    Quick keyword-based relevance filter.
    """
    if not query:
        return items
    
    query_words = set(query.lower().split())
    scored_items = []
    
    for item in items:
        text = item.get('text', '').lower()
        # Count matching words
        score = sum(1 for word in query_words if word in text)
        if score > 0:
            scored_items.append((score, item))
    
    # Sort by relevance score
    scored_items.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored_items]


def query_gemini(system_prompt: str, user_prompt: str) -> dict:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key":
        print("⚠️ Gemini API Key missing or default.")
        return {"error": "Gemini API key not configured", "answer": None}
        
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = model.generate_content(full_prompt)
        
        return {
            "answer": response.text,
            "llm": "gemini-1.5-flash"
        }
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return {"error": str(e), "answer": None}


def query_groq_fallback(system_prompt: str, user_prompt: str) -> dict:
    if not GROQ_API_KEY:
        return {"error": "Groq API key not configured", "answer": None}
        
    try:
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
            "max_tokens": 1000
        }
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        if resp.status_code == 200:
            return {
                "answer": resp.json()["choices"][0]["message"]["content"],
                "llm": "groq-llama-3.3"
            }
    except Exception as e:
        print(f"❌ Groq Error: {e}")
    return {"error": "All LLMs failed", "answer": None}


def pathway_rag_query(context_items: list, question: str) -> dict:
    """
    Enhanced RAG query with:
    1. Freshness filtering (< 5 min)
    2. Keyword relevance filtering
    3. Vector semantic search
    4. Hybrid context building
    """
    
    # === STEP 1: Filter fresh items (< 5 minutes old) ===
    fresh_items = filter_fresh_items(context_items, max_age_seconds=300)
    print(f"📊 Freshness filter: {len(context_items)} → {len(fresh_items)} items")
    
    # === STEP 2: Keyword relevance filter ===
    keyword_matches = filter_relevant_items(fresh_items, question)
    print(f"🔍 Keyword matches: {len(keyword_matches)} items")
    
    # === STEP 3: Vector semantic search ===
    vector_matches = []
    vs = get_vector_store()
    if vs:
        # Add fresh items to vector store
        vs.add_items(fresh_items)
        # Search for semantically similar items
        vector_matches = vs.search(question, n_results=10, max_age_seconds=300)
        print(f"🧠 Vector matches: {len(vector_matches)} items")
    
    # === STEP 4: Hybrid context (combine keyword + vector matches) ===
    seen_urls = set()
    hybrid_context = []
    
    # Priority 1: Keyword matches (most relevant)
    for item in keyword_matches[:15]:
        url = item.get('url', '')
        if url not in seen_urls:
            seen_urls.add(url)
            hybrid_context.append(item)
    
    # Priority 2: Vector matches (semantically similar)
    for item in vector_matches[:10]:
        url = item.get('url', '')
        if url not in seen_urls:
            seen_urls.add(url)
            hybrid_context.append(item)
    
    # Priority 3: Fill remaining with fresh items
    for item in fresh_items[:10]:
        url = item.get('url', '')
        if url not in seen_urls:
            seen_urls.add(url)
            hybrid_context.append(item)
    
    if not hybrid_context:
        # Fallback to most recent items if no matches
        hybrid_context = context_items[-20:]
    
    print(f"📦 Final hybrid context: {len(hybrid_context)} items")
    
    # === STEP 5: Build context string ===
    context_parts = []
    for item in hybrid_context[:25]:
        rel = item.get("reliability", "Unknown")
        created = item.get("created_utc", 0)
        try:
            age_mins = int((time.time() - float(created)) / 60)
            age_str = f"{age_mins} min ago" if age_mins < 60 else f"{age_mins // 60}h ago"
        except:
            age_str = "Unknown time"
        
        context_parts.append(
            f"[Source: {item['source']} | Age: {age_str} | Reliability: {rel}]\n"
            f"{item['text']}\n"
            f"URL: {item.get('url', 'N/A')}"
        )
    
    context_str = "\n\n---\n\n".join(context_parts)
    
    # === STEP 6: System Prompt ===
    system_prompt = """
    You are a high-precision news analyst AI. 
    Analyze the provided context and output a JSON object with the following structure:
    {
        "summary": "A concise executive summary (2-3 sentences).",
        "findings": [
            "Specific key finding 1",
            "Specific key finding 2",
            "Specific key finding 3"
        ],
        "sources": [
            {"source": "Source Name", "headline": "Article Title", "url": "URL"}
        ],
        "reliability": "High/Medium/Low"
    }
    
    RULES:
    - Output RAW JSON only. No Markdown formatting. No ```json blocks.
    - Be objective and factual.
    - "sources" should only include the top 3-5 most relevant items from context.
    - Prioritize RECENT news items (check the "Age" field).
    - If no relevant info is found, return empty arrays and a "No info found" summary.
    """
    
    user_prompt = f"Question: {question}\n\nLIVE CONTEXT (FRESHNESS-FILTERED):\n{context_str}"
    
    # === STEP 7: Query LLM ===
    result = query_gemini(system_prompt, user_prompt)
    if result.get("error"):
        print("🔄 Gemini failed, trying Groq fallback...")
        result = query_groq_fallback(system_prompt, user_prompt)
        
    # === STEP 8: Add metadata ===
    result["sources_analyzed"] = {
        "total": len(context_items),
        "fresh": len(fresh_items),
        "keyword_matches": len(keyword_matches),
        "vector_matches": len(vector_matches),
        "hybrid_context": len(hybrid_context),
        "news": sum(1 for i in hybrid_context if i['source'] in ['newsdata', 'gnews']),
        "social": sum(1 for i in hybrid_context if i['source'] in ['reddit', 'hackernews'])
    }
    
    return result
