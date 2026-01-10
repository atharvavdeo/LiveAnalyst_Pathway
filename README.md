# Live Social Analyst 🤖🌍
### The Pulse of the Internet, Decoded by AI.

**Live Social Analyst** is a high-performance, hybrid RAG (Retrieval-Augmented Generation) engine that aggregates real-time news, social media streams, and historical data to provide instant, context-aware intelligence.

Designed with a **"Verge-style" editorial aesthetic**, it turns raw noise into structured narratives.

![Landing Page](preview_landing.png)

---

## 🏗️ System Architecture

Our architecture is designed for **speed**, **freshness**, and **depth**. It combines immediate live streams with deep historical archives using a custom Hybrid RAG pipeline.

### 1. Multi-Source Ingestion 📡
The system runs parallelized ingestion streams (`ingest/`) that normalize data from diverse sources into a unified schema:
- **NewsAPI (Everything & Headlines)**: Captures global breaking news and viral pop-culture ("Fun Stream").
- **GNews (Historical)**: Provides on-demand access to 1000+ days of historical context for geopolitical queries.
- **Reddit & HackerNews**: Monitors social sentiment and tech discourse in real-time.
- **Firecrawl**: A precision scraper for retrieving deep-web content from specific URLs.

### 2. Hybrid Data Storage 💾
We utilize a dual-layer storage strategy to balance latency and persistence:
- **Hot Storage (In-Memory Deque)**: Stores the last 100-200 live items for sub-millisecond retrieval. Used for the "Live Tick" feed.
- **Cold Storage (SQLite)**: Persists high-value articles and user search history for long-term trend analysis.

### 3. The RAG Pipeline 🧠
Every user query triggers our advanced `pipeline/gemini_rag.py`:

#### A. Vector Embedding
Incoming items are dynamically embedded using `sentence-transformers/all-MiniLM-L6-v2`. This creates a 384-dimensional semantic map of the current news landscape.

#### B. Semantic Indexing (ChromaDB)
We use **ChromaDB (In-Memory)** to index these vectors. This allows the system to understand that "Kremlin" is semantically related to "Russia" and "oil tariffs", retrieving relevant items even if they don't share exact keywords.

#### C. Hybrid Context Construction
The context window sent to the LLM is constructed using a weighted algorithm:
1.  **Freshness Filter**: Prioritizes items < 5 minutes old for live queries.
2.  **Keyword Match (BM25)**: Ensures exact matches (e.g., proper nouns) are included.
3.  **Vector Match**: Pulls in conceptually related items from the wider context.
4.  **Fallback Mechanism**: If GNews returns 0 results (e.g., for niche geopolitical topics), the system automatically falls back to NewsAPI's `everything` endpoint to ensure coverage.

### 4. LLM Synthesis 🤖
The constructed context is sent to **Gemini 1.5 Pro** (or **Llama 3 via Groq** as a robust fallback). The LLM acts as an "Editor-in-Chief", synthesizing disparate facts into:
- **Executive Summary**: A concise 2-3 sentence overview.
- **Key Findings**: Bulleted verification of facts.
- **Reliability Score**: Assessing the credibility of sources.

---

## 📸 App Previews

### 1. The Landing Page
A minimalist, editorial-style entry point featuring a 3D Earth visualization (`cobe`) and architecture breakdown.
![Landing](preview_landing.png)

### 2. The Dashboard (Architecture)
The main interface features a Bento-grid layout, real-time "Internet Curiosities" stream, and live log monitoring.
![Architecture](preview_arch.png)

### 3. AI Search
Glassmorphism-styled search analysis showing the Hybrid RAG engine in action (LLM Summary + Source Citations).
![Search](preview_search.png)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- API Keys: `GEMINI_API_KEY`, `NEWSAPI_KEY`, `GNEWS_API_KEY`

### Installation
```bash
# Clone the repo
git clone https://github.com/YourRepo/LiveSocialAnalyst.git

# Install dependencies
pip install -r requirements.txt
```

### Run
```bash
# Start the FastAPI server (Backend + Frontend)
python app_pathway.py
```
Access the App at `http://localhost:8000/`.

---

## 🛠️ Tech Stack
- **Backend**: FastAPI, Python 3.11
- **AI/ML**: Google Gemini, Groq (Llama 3), ChromaDB, Sentence-Transformers
- **Frontend**: Vanilla JS, HTML5, CSS Variables (Verge Theme)
- **3D Visuals**: Cobe (WebGL Globe)

---

**Powered by Pathway Intelligence.**
