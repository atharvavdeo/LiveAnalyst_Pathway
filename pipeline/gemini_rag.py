import google.generativeai as genai
import yaml
from pathlib import Path
import os
import requests

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
try:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
        GEMINI_API_KEY = config.get("gemini", {}).get("api_key")
        GROQ_API_KEY = os.getenv("GROQ_API_KEY") # Keep Groq as backup env var
except Exception as e:
    print(f"⚠️ Error loading config for Gemini: {e}")
    GEMINI_API_KEY = None

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
                "answer": resp.json()["choices"][0]["message"]["content"] + "\n\n_[Fallback: Powered by Groq]_",
                "llm": "groq-llama-3.3"
            }
    except Exception:
        pass
    return {"error": "All LLMs failed", "answer": None}

def pathway_rag_query(context_items: list, question: str) -> dict:
    # 1. Build Context
    context_parts = []
    for item in context_items[-30:]: # Use last 30 items
        rel = item.get("reliability", "Unknown")
        context_parts.append(
            f"[Source: {item['source']} | Reliability: {rel}]\n"
            f"{item['text']}\n"
            f"URL: {item.get('url', 'N/A')}"
        )
    
    context_str = "\n\n---\n\n".join(context_parts)
    
    # 2. System Prompt
    system_prompt = """You are a Real-Time News Analyst.
    Base your answer ONLY on the provided live context data.
    
    OUTPUT FORMAT (Markdown):
    
    ## 📊 Analysis Summary
    Brief summary.
    
    ## 📰 Relevant Sources
    | # | Source | Reliability | Headline | Link |
    |---|--------|-------------|----------|------|
    | 1 | ...    | ...         | ...      | ...  |
    
    ## 🔍 Key Findings
    - **Finding**: ...
    
    ## 📈 Reliability
    - Verified Sources: X
    - Community/Social: Y
    
    ## 💡 Conclusion
    Final verdict.
    """
    
    user_prompt = f"Question: {question}\n\nLIVE CONTEXT:\n{context_str}"
    
    # 3. Query Gemini with Fallback
    result = query_gemini(system_prompt, user_prompt)
    if result.get("error"):
        print("🔄 Gemini failed, trying Groq fallback...")
        result = query_groq_fallback(system_prompt, user_prompt)
        
    # 4. Add metadata
    result["sources_analyzed"] = {
        "total": len(context_items),
        "news": sum(1 for i in context_items if i['source'] in ['newsdata', 'gnews']),
        "social": sum(1 for i in context_items if i['source'] in ['reddit', 'hackernews'])
    }
    
    return result
