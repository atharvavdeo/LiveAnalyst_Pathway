# System Architecture: LiveSocialAnalyst

## Overview
LiveSocialAnalyst is a **Hybrid RAG (Retrieval-Augmented Generation)** system that combines real-time data streaming with historical searching and persistent storage to provide up-to-the-minute analysis of news and social trends.

## High-Level Diagram
```mermaid
graph TD
    User[User Frontend] -->|Polls| API[FastAPI Backend]
    User -->|Selects Category| Dynamic[Dynamic Fetcher]
    User -->|Query| RAG[RAG Pipeline]

    subgraph "Data Ingestion (Hybrid)"
        NewsAPI[NewsAPI.org] -->|Live Stream| Buffer[In-Memory Deque]
        GNews[GNews.io] -->|Live Stream| Buffer
        Social[HackerNews/Reddit] -->|Live Stream| Buffer
        Firecrawl[Firecrawl (Web)] -->|On-Demand| VectorStore
    end

    subgraph "Persistence & Search"
        Buffer -->|Batch Write| SQL[SQLite Database]
        Dynamic -->|Fetch| NewsAPI
        Dynamic -->|Save| SQL
        RAG -->|Context| VectorStore[ChromaDB]
        RAG -->|History| SQL
    end

    subgraph "AI Synthesis"
        VectorStore -->|Relavant Context| LLM[Gemini/Groq]
        LLM -->|Answer| API
    end
```

## Core Components

### 1. Ingestion Layer (`ingest/`)
Handles connection to external APIs. Runs on background threads.
- **Connectors**: `NewsApiConnector`, `GNewsConnector`, `HackerNewsConnector`, `FirecrawlConnector`.
- **Mode**: Continuous Polling (Live) + On-Demand fetching (Targeted).

### 2. Orchestration Layer (`app_pathway.py`)
The central nervous system.
- **FastAPI**: Serves the Frontend and API endpoints.
- **Data Store**: Maintains a sliding window (`deque`) of the latest 200 items for instant "Feed" display.
- **Endpoints**:
    - `/data`: Returns live stream stats and recent items.
    - `/fetch_news`: Proxies specific category requests to NewsAPI.
    - `/query`: Triggers the RAG pipeline.

### 3. RAG Pipeline (`pipeline/gemini_rag.py`)
Synthesizes answers from diverse data sources.
- **Vector Search**: Uses `SentenceTransformer` to encode content and `ChromaDB` (ephemeral) to retrieve relevant chunks.
- **Hybrid Context**: Merges **Live Data** (RAM) + **Historical Data** (SQLite) + **Web Search** (Firecrawl) before answering.

### 4. Persistence Layer (`data/database.py`)
Ensures no data is lost.
- **SQLite**: Stores every fetched article with a unique URL constraint.
- **Deduplication**: Prevents storing the same article twice.

## Key Workflows

### A. The "Live Feed"
1. Connectors fetch data every 15-60 minutes.
2. Data is pushed to `data_store` (RAM) for instant serving.
3. Data is batched and saved to `news_archive.db` (Disk).

### B. The "Analyst Query"
1. User asks: "Impact of inflation on tech stocks?"
2. System checks `news_archive.db` for past articles.
3. System triggers `search_historical()` (GNews) and `scrape_targeted()` (Firecrawl) for fresh depth.
4. All text is embedded -> Top 10 chunks retrieved -> LLM generates simple report.
