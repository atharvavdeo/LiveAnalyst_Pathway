# Live Social Analyst | Real-Time Pathway ETL Intelligence

[![Pathway](https://img.shields.io/badge/Powered%20by-Pathway-blue)](https://github.com/pathwaycom/pathway)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/AI-Groq%20Llama%203-orange)](https://groq.com)
[![Gemini](https://img.shields.io/badge/AI-Gemini%203.0-blue)](https://deepmind.google/technologies/gemini/)

##  The Problem with Stale Knowledge
In the current landscape of artificial intelligence, many applications powered by Large Language Models (LLMs) are constrained by a fundamental limitation: **their knowledge is static**. Retrieval-Augmented Generation (RAG) systems, while powerful, often rely on a knowledge base that is a mere snapshot in time.

This creates a **"knowledge cutoff,"** where an AI assistant can become instantly obsolete. Imagine a financial chatbot unaware of a market-moving announcement made minutes ago, or a customer service bot providing information based on documentation that was updated yesterday. In a world that operates in real-time, **these delays are critical failures**.

##  The Paradigm Shift to "Live AI"
A new paradigm is emerging to address this challenge: **"Live AI."** This represents a fundamental shift from static, retrospective intelligence to dynamic systems that perceive, learn, and reason in real-time.

**Live Social Analyst** is perpetually synchronized with the latest version of reality, processing information as it is created, modified, or deleted. This project puts us at the forefront of this transformation.

##  Powered by Pathway: The Engine for Live AI
The core technology driving this application is **Pathway**, a data processing framework designed specifically for building AI pipelines over **live data streams**.

It allows us to define complex AI workflows that process information **incrementally**, enabling extremely low-latency updates. Its unique architecture unifies batch and streaming data, meaning we can ingest thousands of global sources and instantly reflect them in our RAG pipeline without manual restarts or batch re-indexing.

---

##  How It Works: The "Live AI" Pipeline

This application connects to a dynamic, continuously updating array of data sources and reflects the **absolute latest state of reality** in real-time.

1.  **Massive Real-Time Ingestion**:
    *   **1000+ RSS Feeds (OPML)**: Continuously scanning global news.
    *   **NewsData.io & GNews**: Integrating external news APIs.
    *   **HackerNews & Social Streams**: Monitoring tech & social discussions.

2.  **Zero-Latency Processing**:
    *   As soon as a news item is detected, it is **instantly streamed** into the Pathway engine.
    *   The engine deduplicates, normalizes, and embeds the text on-the-fly.
    *   New information is **immediately indexable** by the RAG system—no waiting for nightly batches.

3.  **Dynamic Context Retrieval**:
    *   When you ask a question ("What just happened in Tech?"), the RAG pipeline queries the **live index**.
    *   It retrieves context that may have been created **seconds ago**.
    *   The LLM generates an answer based on what is happening *right now*, not what happened yesterday.


## 📸 App Previews
<div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
    <img src="preview_landing.png" width="30%" alt="Live Dashboard" style="border-radius:8px; border:1px solid #333;" />
    <img src="preview_search.png" width="30%" alt="RAG Search" style="border-radius:8px; border:1px solid #333;" />
    <img src="preview_arch.png" width="30%" alt="Architecture" style="border-radius:8px; border:1px solid #333;" />
</div>

## 🛠️ Integrated Pathway Technologies

This project strictly adheres to the **Pathway Live Data Framework**, utilizing specific APIs to achieve millisecond-latency streaming.

### 1. Unified Data Ingestion (`pw.io`)
We don't use batch scraping. We use **Pathway Connectors** to turn APIs into streaming tables:
*   **RSS/OPML Stream**: Implemented using `pw.io.python.read` to wrap our asyncio-based OPML fetcher as a continuous Table stream.
*   **API Streams**: Twitter/X and NewsData.io are ingested via custom connectors extending Pathway's input schema.

### 2. Live Transformations (`pw.temporal` & `pw.state`)
The engine processes data incrementally:
*   **Incremental Deduplication**: We use `pw.io.deduplicate(pathway.table)` to merge identical stories (by title/content similarity) arriving from different feeds in real-time.
*   **Sliding Window Aggregation**: `pw.temporal.sliding` is used to group news items by 5-minute windows to detect sudden "virality spikes" across multiple sources.

### 3. Real-Time RAG (`pw.xpacks.llm`)
*   **Vector Indexing**: Incoming text is embedded using `pw.xpacks.llm.embedders` (Gemini/HuggingFace) and indexed in a live KNN index.
*   **Context Retrieval**: Queries are executed against this live index using `pw.xpacks.llm.retrievers`, ensuring the context includes data from *milliseconds ago*.

### Architecture Diagram
```mermaid
graph LR
    User[User Frontend]
    API[FastAPI Backend]

    subgraph Inputs ["Pathway Connectors (Custom)"]
        direction TB
        OPML["OPML Stream<br/>(pw.io.python.read)"]
        NewsData["NewsData Stream"]
        Social["Social Stream"]
    end

    subgraph Core ["Pathway ETL Engine"]
        direction TB
        Dedup[Incremental Dedup]
        Window[Sliding Windows]
        Vector[Live Vector Index]
    end

    subgraph AI ["LLM xPack"]
        direction TB
        RAG[Real-Time RAG]
        Gen[Gemini 1.5 Generated]
    end

    Inputs -->|Stream| Core
    Core -->|Transform| Vector
    Vector -->|Retrieve| AI
    User --> API
    API --> AI
    AI --> API
    API --> User
```

## 🧠 Deep Dive: The Life of a Data Point
This detailed sequence diagram illustrates exactly how a news item travels from a source to the LLM in milliseconds, highlighting the **Pathway Engine's internal mechanics**.

```mermaid
sequenceDiagram
    autonumber
    participant Internet as "Refreshed Data Source"
    participant Connector as "Pathway Connector"
    participant InputTable as "pw.Table (Input)"
    participant Transform as "Transformation Engine"
    participant State as "Global Deduplication State"
    participant Vector as "KNN Vector Index"
    participant User as "User Query"
    participant RAG as "RAG Retriever"

    Note over Internet, Connector: T+0ms: News Published
    Internet->>Connector: Poll/Stream New Item
    Connector->>InputTable: Append Row (JSON)
    
    Note over InputTable, Transform: STREAMING MODE
    InputTable->>Transform: Propagate Update (New Row)
    
    Transform->>State: Check Existence (URL/Title Hash)
    alt Is Duplicate?
        State-->>Transform: TRUE (Ignore)
    else Is New?
        State-->>Transform: FALSE (Process)
        Transform->>Transform: Text Normalization & Cleaning
        Transform->>Transform: Compute Embeddings (Gemini)
        Transform->>Vector: UPSERT Vector
    end
    
    Note over Vector, User: T+200ms: Ready for Query
    
    User->>RAG: "What just happened?"
    RAG->>Vector: KNN Search (k=5)
    Vector-->>RAG: Return Top Matches
    RAG->>User: Generate Answer with Context
```

---

## Installation & Usage

Follow these steps to deploy the system locally.

### 1. Prerequisites
*   **Python**: Version 3.10 or higher.
*   **API Keys**: You need keys for:
    *   **Gemini** (Google AI)
    *   **Groq** (Llama 3 Inference)
    *   **GNews** (Historical Data)

### 2. Configuration
1.  Clone the repository:
    ```bash
    git clone https://github.com/your-repo/LiveSocialAnalyst.git
    cd LiveSocialAnalyst
    ```
2.  Create a `.env` file (or update `config.yaml`) with your credentials:
    ```env
    GEMINI_API_KEY=your_key_here
    GROQ_API_KEY=your_key_here
    GNEWS_API_KEY=your_key_here
    ```

### 3. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Execution
Run the main application script. This initializes the FastAPI server and spawns the background Pathway daemon threads.

```bash
python3 app_pathway.py
```
*Expected Output*:
> `INFO: Uvicorn running on http://0.0.0.0:8000`
> ` OPML: Starting to parse 2000+ RSS feeds...`
> ` Injected 10 High-Frequency Firehose Feeds.`

---

## API Endpoints Reference

The system exposes a RESTful API for frontend integration and external webhooks.

| Method | Endpoint | Description | Payload / Params |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Landing Page | None |
| `GET` | `/app` | Main Dashboard Application | None |
| `GET` | `/data` | Fetch current engine stats and real-time buffer (No-Cache) | None |
| `POST` | `/fetch_news` | Get categorical news (Business, Tech, etc.) | `{"category": "business"}` |
| `POST` | `/query` | Perform RAG Analysis (Search) | `{"query": "Trump"}` |
| `POST` | `/refresh_opml` | **Burst Signal**: Triggers "Firehose" instant ingestion | None |

---

## Project Structure

A clean, modular architecture designed for scalability.

```
LiveSocialAnalyst/
├── app_pathway.py         # MAIN ENTRY POINT: Server & Thread Orchestrator
├── config.yaml            # Global Configuration
├── requirements.txt       # Dependency List
├── .env                   # Secrets (GitIgnored)
│
├── ingest/                # PATHWAY CONNECTORS (Data Ingestion)
│   ├── opml_loader.py     # High-Throughput Burst Ingestor
│   ├── gnews_connector.py
│   ├── firecrawl_connector.py
│   ├── reddit_stream.py
│   └── hackernews_stream.py
│
├── pipeline/              # INTELLIGENCE LAYER
│   └── gemini_rag.py      # Hybrid RAG & LLM Logic
│
├── frontend/              # PRESENTATION LAYER
│   ├── index.html         # Main SPA Real-Time Dashboard
│   └── assets/
│
└── data/                  # PERSISTENCE LAYER
    ├── database.py        # SQLite Interface
    └── storage/           # Local vector stores
```

---

## License
MIT License. Built for High-Performance Data Engineering.
