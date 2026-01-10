# LiveSocialAnalyst - Pathway Edition 🚀

Real-time news and social media analysis powered by **Pathway's streaming framework** with AI-powered reliability scoring.

![LiveSocialAnalyst UI](https://raw.githubusercontent.com/atharvavdeo/LiveAnalyst_Pathway/main/preview.png)

## ✨ Features

- **🔶 Pathway Streaming**: Real-time data ingestion from NewsData.io and HackerNews
- **🤖 AI Analysis**: GPT-4o-mini with Groq (Llama 3.3) fallback
- **📊 Structured Output**: Tabular source citations with reliability scoring
- **🎨 Surreal White UI**: Beautiful, modern glassmorphic design
- **✅ Reliability Indicators**:
  - ✅ VERIFIED - Official news sources
  - 🔶 COMMUNITY - HackerNews tech discussions

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

## 🔑 API Keys Required

| Key | Required | Get it at |
|-----|----------|-----------|
| NEWSDATA_API_KEY | ✅ | https://newsdata.io |
| GROQ_API_KEY | ✅ | https://console.groq.com/keys (FREE) |
| OPENAI_API_KEY | Optional | https://platform.openai.com |

## 📁 Architecture

```
├── app_pathway.py       # Main Pathway + FastAPI hybrid app
├── frontend/index.html  # Surreal white UI
├── ingest/              # Data ingestion streams
│   ├── hackernews_stream.py
│   └── news_api.py
├── pipeline/            # Processing pipeline
│   ├── reliability.py   # Source scoring
│   └── rag.py
└── requirements.txt
```

## 📖 How It Works

1. **Pathway Streaming Worker** continuously fetches news + HackerNews
2. **Data is scored** for reliability (news=high, HN=medium)
3. **User queries** trigger RAG against streamed context
4. **AI generates** structured analysis with source tables

## 🧪 203 Questions Test

Click the "Run 203 Questions Test" button to benchmark the system.

---

Built with ❤️ using Pathway, FastAPI, and Groq
