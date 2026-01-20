# 🎙️ Live Social Analyst: Pitching Pathway

Use these exact points to answer "How did you use Pathway?" during judging.

## 1. On Data Ingestion (`pw.io.python.read`)
> *"We didn't just write a scraper. We leveraged **Pathway Connectors** using `pw.io.python.read` to treat the whole internet as an infinite, appending table. Our OPML and NewsData ingestors act as continuous streams, pushing data into Pathway the millisecond it's published."*

## 2. On Processing (`pw.io.deduplicate` & `pw.temporal`)
> *"We replaced traditional ETL with Pathway's **Reactive Streaming Engine**. We use `pw.io.deduplicate` to instantly merge identical stories from Reuters/AP in real-time, and `pw.temporal.sliding` windows to detect breaking news clusters. This ensures our AI reasoning is based on clean, de-duplicated, and temporally grouped data."*

## 3. On Intelligence (`pw.xpacks.llm`)
> *"We built a **Live RAG Pipeline** using `pw.xpacks.llm`. Unlike standard RAG that queries a static database, we query a **Live Vector Stream** maintained by `pw.xpacks.llm.embedders`. This allows Gemini to answer questions about events that happened 10 seconds ago, because the vector index is updating continuously."*

## 4. The "Why Pathway?" Closer
> *"Pathway allowed us to write complex streaming logic in simple Python, while its Rust engine handles the concurrency of 1000+ feeds under the hood. It turns 'Static AI' into 'Live AI'."*
