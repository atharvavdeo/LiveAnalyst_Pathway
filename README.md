# Live Social Analyst

**Live Social Analyst** is a high-performance, hybrid RAG (Retrieval-Augmented Generation) engine that aggregates real-time news, social media streams, and historical data to provide instant, context-aware intelligence.

## System Architecture

The system is architected around the **Pathway Data Stream**, a high-throughput ingestion layer that enables the system to process live information with sub-second latency while maintaining deep historical context.

### Architecture Diagram
```mermaid
graph TD
    User[User Frontend] -->|Polls| API[FastAPI Backend]
    User -->|Query| RAG[RAG Pipeline]

    subgraph "Pathway Data Stream (Ingestion)"
        NewsAPI[NewsAPI.org] -->|Live Stream| Buffer[In-Memory Deque]
        GNews[GNews.io] -->|Live Stream| Buffer
        Social["HackerNews/Reddit"] -->|Live Stream| Buffer
        Firecrawl["Firecrawl (Web)"] -->|On-Demand| VectorStore
    end

    subgraph "Persistence & Search"
        Buffer -->|Batch Write| SQL[SQLite Database]
        RAG -->|Context| VectorStore[ChromaDB]
        RAG -->|History| SQL
    end

    subgraph "AI Synthesis"
        VectorStore -->|Relevant Context| LLM["Gemini/Groq"]
        LLM -->|Answer| API
    end
```

### 1. Pathway Data Stream (Ingestion Layer)
The Pathway Data Stream acts as the central nervous system for data, managing parallel ingestion pipelines from diverse high-velocity sources:
- **NewsAPI Streams**: Captures global breaking news and specific topic streams (e.g., "Fun/Viral" stream) in real-time.
- **GNews Historical Bridge**: Provides on-demand access to a 3-year archive for deep context on geopolitical and economic queries.
- **Social Firehose**: Ingests rapid-fire sentiment data from Reddit and HackerNews.
- **Firecrawl Targeted Scraper**: Executes precision deep-web scraping for specific URLs or semantic targets.

All incoming data is normalized instantaneously into a unified schema within the Pathway Data Stream before being routed to the storage layer.

### 2. Hybrid Data Storage
The architecture utilizes a tiered storage strategy to optimize for both freshness and persistence:
- **Hot Storage (In-Memory)**: The Live Stream buffer holds the most recent data points in memory for immediate access by the RAG engine.
- **Cold Storage (SQLite)**: High-value articles and historical search results are persisted to a relational database for long-term trend analysis and auditability.

### 3. The Hybrid RAG Pipeline
Every user query triggers a sophisticated retrieval pipeline designed to maximize relevance and accuracy:

#### A. Vector Embedding & Indexing
Incoming items from the Pathway Data Stream are embedded using `sentence-transformers/all-MiniLM-L6-v2`, creating a 384-dimensional vector representation. These vectors are indexed in **ChromaDB (In-Memory)**, enabling semantic search capabilities that go beyond simple keyword matching.

#### B. Context Construction Algorithm
The RAG engine constructs the context window for the LLM using a multi-factor ranking algorithm:
1.  **Freshness Filter**: Prioritizes live data items (less than 5 minutes old) for real-time queries.
2.  **Semantic Vector Search**: Retrieves items that are conceptually related to the query, even without exact keyword matches.
3.  **Keyword Boosting**: Ensures items with exact name matches are included to prevent hallucination.
4.  **Fallback Mechanism**: Automatically triggers secondary data providers (e.g., NewsAPI fallback) if primary historical sources yield insufficient data.

### 4. LLM Synthesis
The constructed context is processed by **Gemini 1.5 Pro** (or **Llama 3 via Groq**) to generate the final intelligence output. The LLM synthesizes the retrieval set into an Executive Summary and verified Key Findings, citing specific sources from the data stream.

---

## App Previews

### Landing Page
A minimalist entry point featuring a 3D data visualization and architectural overview.
![Landing Page](preview_landing.png)

### The Dashboard
The main interface featuring the real-time Pathway Data Stream and Bento-grid layout.
![Dashboard Architecture](preview_arch.png)

### Intelligent Search
The Hybrid RAG analysis view showing synthesized intelligence and reliability scoring.
![Search Analysis](preview_search.png)

---

## Getting Started

### Prerequisites
- Python 3.10+
- API Keys: `GEMINI_API_KEY`, `NEWSAPI_KEY`, `GNEWS_API_KEY`

### Installation
```bash
# Clone the repository
git clone https://github.com/YourRepo/LiveSocialAnalyst.git

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Start the FastAPI server (Backend + Frontend)
python app_pathway.py
```
Access the application at `http://localhost:8000/`.

---

## Tech Stack
- **Backend Frameowrk**: FastAPI
- **Language**: Python 3.11
- **LLM Orchestration**: Google Gemini, Groq (Llama 3)
- **Vector Database**: ChromaDB
- **Embeddings**: Sentence-Transformers
- **Frontend**: Native JS, HTML5, CSS Variables
