# LiveNewsAnalyst -  using Pathway

Real-time news and social media analysis powered by **Pathway's streaming framework** with AI-powered reliability scoring.

##  Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LiveSocialAnalyst                                  │
│                         Pathway + FastAPI Hybrid                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  📰 NewsData  │          │  🔶 HackerNews │          │  🌐 Frontend  │
│     API       │          │      API       │          │   (HTML/JS)   │
│  (Official)   │          │  (Community)   │          │  Surreal UI   │
└───────┬───────┘          └───────┬───────┘          └───────┬───────┘
        │                          │                          │
        └──────────────┬───────────┘                          │
                       ▼                                      │
        ┌──────────────────────────┐                          │
        │   🔄 Pathway Streaming   │                          │
        │      Worker Thread       │                          │
        │  ┌────────────────────┐  │                          │
        │  │ Real-time Ingest   │  │                          │
        │  │ • 2-min intervals  │  │                          │
        │  │ • Deque storage    │  │                          │
        │  └────────────────────┘  │                          │
        └──────────────┬───────────┘                          │
                       ▼                                      │
        ┌──────────────────────────┐                          │
        │  📊 Reliability Scoring  │                          │
        │  ┌────────────────────┐  │                          │
        │  │ ✅ News = HIGH     │  │                          │
        │  │ 🔶 HN = MEDIUM     │  │                          │
        │  │ ⚠️ Social = LOW    │  │                          │
        │  └────────────────────┘  │                          │
        └──────────────┬───────────┘                          │
                       ▼                                      │
        ┌──────────────────────────┐                          │
        │   🧠 LLM RAG Query       │◄─────────────────────────┘
        │  ┌────────────────────┐  │      POST /query
        │  │ Context Builder    │  │
        │  │ (25 recent items)  │  │
        │  └────────┬───────────┘  │
        │           ▼              │
        │  ┌────────────────────┐  │
        │  │ OpenAI GPT-4o-mini │  │
        │  │        OR          │  │
        │  │ Groq Llama 3.3     │  │
        │  │   (Fallback)       │  │
        │  └────────────────────┘  │
        └──────────────┬───────────┘
                       ▼
        ┌──────────────────────────┐
        │  📋 Structured Output    │
        │  ┌────────────────────┐  │
        │  │ • Analysis Summary │  │
        │  │ • Sources Table    │  │
        │  │ • Key Findings     │  │
        │  │ • Reliability %    │  │
        │  │ • Conclusion       │  │
        │  └────────────────────┘  │
        └──────────────────────────┘
```

## ✨ Features

- ** Pathway Streaming**: Real-time data ingestion from NewsData.io and HackerNews
- ** AI Analysis**: GPT-4o-mini with Groq (Llama 3.3) fallback
- ** Structured Output**: Tabular source citations with reliability scoring
- ** Surreal White UI**: Beautiful, modern glassmorphic design
- ** Reliability Indicators**:
  -  VERIFIED - Official news sources
  -  COMMUNITY - HackerNews tech discussions

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/atharvavdeo/LiveAnalyst_Pathway.git
cd LiveAnalyst_Pathway

# Setup
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python app_pathway.py
```

Then open http://localhost:8000

##  API Keys Required

| Key | Required | Get it at |
|-----|----------|-----------|
| NEWSDATA_API_KEY |  | https://newsdata.io |
| GROQ_API_KEY |  | https://console.groq.com/keys (FREE) |
| OPENAI_API_KEY | Optional | https://platform.openai.com |

##  Project Structure

```
LiveAnalyst_Pathway/
├── app_pathway.py       # Main Pathway + FastAPI hybrid app
├── frontend/
│   └── index.html       # Surreal white UI with styled AI output
├── ingest/              # Data ingestion modules
│   ├── hackernews_stream.py
│   └── news_api.py
├── pipeline/            # Processing pipeline
│   ├── reliability.py   # Source scoring
│   └── rag.py           # RAG implementation
├── .env.example         # Environment template
├── requirements.txt     # Python dependencies
└── README.md
```

##  How It Works

1. **Pathway Streaming Worker** continuously fetches news + HackerNews (2-min intervals)
2. **Data is scored** for reliability (news=HIGH, HN=MEDIUM)
3. **User queries** trigger RAG against 25 most recent items
4. **AI generates** structured analysis with source tables and reliability breakdowns
5. **Frontend renders** beautiful styled output with gradient headers and cards

---

