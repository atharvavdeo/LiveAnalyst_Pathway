# Live Social Analyst | 24/7 Real-Time Intelligence

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/AI-Groq%20Llama%203-orange)](https://groq.com)
[![Gemini](https://img.shields.io/badge/AI-Gemini%201.5-blue)](https://deepmind.google/technologies/gemini/)

**Live Social Analyst** is a high-performance, real-time intelligence engine designed to aggregate, deduplicate, and analyze global information streams instantly. It combines a massive ingestion network (1800+ RSS feeds, NewsAPI, GNews, Reddit, HackerNews) with a Hybrid RAG (Retrieval-Augmented Generation) pipeline to answer complex queries like "What is happening with Shark Tank right now?" with verifiable sources.

## 🚀 Key Features

*   **☢️ "Nuclear Option" Ingestion**: Simultaneously streams data from **1800+ Global RSS feeds** (OPML) alongside premium APIs. [See Architecture](OPML_ARCHITECTURE.md).
*   **🔴 Real-Time "Fetch Live"**: Front-end button triggers an immediate, interrupt-driven refresh of the backend engine, ensuring sub-second data freshness.
*   **🧠 Hybrid RAG Pipeline**:
    *   **Retrieval**: Combines live memory buffers (Hot) with historical SQLite storage (Cold).
    *   **Generation**: Uses **Gemini 1.5 Flash** with automatic failover to **Groq (Llama 3)** for resilience.
*   **🛡️ Intelligent Deduplication**: Filter logic removes duplicate stories across different sources to keep the feed clean.
*   **🏷️ Topic isolation**: Strict category filtering allows users to isolate "Business", "Tech", or "Science" streams without noise.

---

## 🏗️ System Architecture

The system uses a **Multithreaded Producer-Consumer Architecture** to handle high-velocity data without blocking the API.

### Architecture Diagram
```mermaid
graph TD
    User[User Frontend] -->|Polls/Fetch| API[FastAPI Backend]
    User -->|Query "Shark Tank"| RAG[Analysis Pipeline]

    subgraph "Ingestion Engine (Daemon Threads)"
        NewsAPI[NewsAPI.org] -->|Thread 1| Buffer[Live Memory Deque]
        GNews[GNews.io] -->|Thread 2| Buffer
        Social["Reddit/HN"] -->|Thread 3| Buffer
        OPML["OPML Nuclear (1800+)"] -->|Thread 4 (Global)| Buffer
    end

    subgraph "Control Plane"
        User -->|Click 'Fetch Live'| RefreshEP[/refresh_opml]
        RefreshEP -->|Signal| OPML
        OPML -->|Force Restart| Web[The Internet]
    end

    subgraph "AI Synthesis"
        Buffer -->|Context| LLM["Gemini / Groq"]
        LLM -->|Summary & Finds| API
    end
```

### 1. Ingestion Layer
Instead of relying on heavy external frameworks, we implemented a custom **Python Threading** engine. Each connector (News, Social, OPML) runs in its own daemon thread, fetching data and pushing it to a thread-safe `deque`.
*   **OPML Engine**: See [OPML_ARCHITECTURE.md](OPML_ARCHITECTURE.md) for details on the "Nuclear" mass-ingestion system.

### 2. RAG & AI Layer
*   **Model A (Primary)**: Gemini 1.5 Flash (Google) - Fast, large context.
*   **Model B (Fallback)**: Groq (Llama 3.3 70B) - Ultra-low latency inference.
*   **Vector Search**: (Currently disabled to prevent threading deadlocks, relying on Keyword + Time-Decay Re-ranking).

---

## 🛠️ Installation & Usage

### Prerequisites
*   Python 3.10+
*   API Keys: Gemini, Groq, NewsAPI, GNews (configured in `.env` and `config.yaml`).

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Backend
```bash
# Starts FastAPI server on port 8000
python3 app_pathway.py
```
*   **Note**: The server logs will show "🚀 OPML: Starting to parse..." indicating the engine is warming up.

### 3. Access the Frontend
Open `frontend/index.html` in your browser, or visit:
`http://localhost:8000/app`

### 4. How to Use
1.  **View Feed**: The main page shows a "Verge-style" Bento grid of top news.
2.  **Filter Topics**: Click "Business", "Tech", etc. in the startup modal or header.
3.  **🔴 Fetch Live**: Click the pink button in the header.
    *   *Action*: This forces the backend to DROP the current OPML cycle and restart scanning 1800+ feeds immediately.
    *   *Result*: A modal appears with the absolute latest 10 items from around the world.
4.  **Ask AI**: Use the search bar (e.g., "Shark Tank").
    *   *Result*: The system aggregates relevant live items and generates a briefing.

---

## 📂 Project Structure

*   `app_pathway.py`: Main entry point, API, and Thread Manager.
*   `ingest/`: Connector modules (OPML, NewsAPI, Reddit, etc.).
*   `pipeline/`: RAG logic and LLM integration (`gemini_rag.py`).
*   `frontend/`: Static HTML/JS UI (`index.html`).
*   `data/`: SQLite database and local caches.
*   `OPML_ARCHITECTURE.md`: Detailed docs for the ingestion engine.

---

## 📜 License
MIT License. Built for the Pathway Datathon (and beyond).
