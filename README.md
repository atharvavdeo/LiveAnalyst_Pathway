# LiveNewsAnalyst

Real-time news and social media analysis powered by Pathway streaming framework with AI reliability scoring.

## Architecture

This application uses a hybrid architecture combining Pathway's real-time data processing with FastAPI. It ingests data from multiple sources, processes it for reliability, and serves AI-analyzed insights via a web interface.

### System Diagram

```
[ Sources ]
    |
    |-- NewsData.io (Official News)
    |-- GNews API (Global Headlines)
    |-- HackerNews (Tech Community)
    |-- Reddit (Social Discussion)
    |
    v
[ Data Ingestion Layer ]
    |
    |-- Polling Connectors (NewsData, GNews)
    |-- Real-time Streams (HackerNews, Reddit)
    |
    v
[ Pathway Processing ]
    |
    |-- Data Normalization
    |-- Reliability Scoring (High/Medium/Low)
    |-- In-Memory Storage (Deque)
    |
    v
[ AI Analysis Engine ]
    |
    |-- RAG Context Builder (Recent 40 items)
    |-- Gemini Pro (Primary LLM)
    |-- Groq Llama 3.3 (Fallback LLM)
    |
    v
[ Frontend Interface ]
    |
    |-- FastAPI Serving
    |-- Real-time Dashboard
    |-- Structured Analysis Output
```

## Features

- **Multi-Source Ingestion**: Aggregates data from NewsData.io, GNews, HackerNews, and Reddit.
- **Reliability Scoring**: Automatically categorizes sources as High (News), Medium (Specialized Communities), or Low (General Social Media).
- **Dual AI Engine**: Uses Gemini Pro for primary analysis with automatic fallback to Groq (Llama 3.3) for robustness.
- **Real-time Context**: Analysis is based on a live window of the most recent data points.
- **Structured IO**: Outputs clear, tabular data with verification status and source links.

## Configuration

Configuration is managed via `config.yaml` for API keys and `app_pathway.py` for pipeline settings.

### Required API Keys

1.  **NewsData.io**: For general news coverage.
2.  **GNews**: For top global headlines.
3.  **Gemini (Google)**: For primary AI analysis.
4.  **Reddit**: For social sentiment (optional).

## Quick Start

1.  **Clone the repository**
    ```bash
    git clone https://github.com/atharvavdeo/LiveAnalyst_Pathway.git
    cd LiveAnalyst_Pathway
    ```

2.  **Install Dependencies**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure API Keys**
    Edit `config.yaml` with your API credentials:
    ```yaml
    gemini:
      api_key: "YOUR_KEY"
    gnews:
      api_key: "YOUR_KEY"
    newsdata:
      api_key: "YOUR_KEY"
    ```

4.  **Run the Application**
    ```bash
    python app_pathway.py
    ```

5.  **Access Dashboard**
    Open `http://localhost:8000` in your browser.

## Project Structure

- `app_pathway.py`: Main application entry point and pipeline orchestration.
- `config.yaml`: Central configuration for API keys.
- `ingest/`: Data connector modules for each source.
    - `newsdata_connector.py`
    - `gnews_connector.py`
    - `hackernews_stream.py`
    - `reddit_stream.py`
- `pipeline/`: Core logic for RAG and AI interaction.
    - `gemini_rag.py`: Handling Gemini/Groq queries.
- `frontend/`: Web interface assets.

## Data Flow

1.  Connectors fetch data from their respective APIs.
2.  Data is normalized into a common schema (Source, Text, URL, Timestamp, Reliability).
3.  Items are pushed to a central thread-safe storage.
4.  User queries trigger the RAG engine.
5.  The system retrieves relevant context from the live window.
6.  The AI model generates a structured response citing specific sources.
