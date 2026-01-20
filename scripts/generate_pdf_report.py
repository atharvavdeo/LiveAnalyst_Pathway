from fpdf import FPDF
import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Live Social Analyst - Project Documentation', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 5, body)
        self.ln()

pdf = PDF()
pdf.alias_nb_pages()
pdf.add_page()

# Title Page
pdf.set_font('Arial', 'B', 24)
pdf.cell(0, 40, 'Live Social Analyst', 0, 1, 'C')
pdf.set_font('Arial', '', 14)
pdf.cell(0, 10, 'The "Live AI" Engine for Real-Time Global Pulse', 0, 1, 'C')
pdf.cell(0, 10, 'Pathway Datathon Submission', 0, 1, 'C')
pdf.ln(20)
pdf.set_font('Arial', 'I', 11)
pdf.cell(0, 10, f'Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
pdf.add_page()

# 1. Documentation & Architecture
pdf.chapter_title('1. Documentation & Architecture')
pdf.chapter_body("""
High-Level Architecture:
Live Social Analyst is a real-time Retrieval-Augmented Generation (RAG) system powered by Pathway. It ingests live data from thousands of sources, processes it incrementally, and enables an LLM to answer questions about events happening right now.

Core Components:
1. Inputs: 
   - 34 OPML Files (1000+ RSS Feeds)
   - NewsData.io API
   - GNews API & HackerNews
   - Twitter/X API (Ready)

2. Pathway ETL Engine:
   - Ingests streams in real-time
   - Deduplicates identical stories
   - Normalizes text and metadata
   - Managing consistency and out-of-order data

3. Storage & Retrieval:
   - Hybrid Vector Store: In-memory live buffer for 0-latency access
   - SQLite Archive: For historical persistence and complex filtering
   - RAG Pipeline: Finds relevant context based on user queries

4. AI & Inference:
   - LLM: Gemini 1.5 Flash (Primary) / Groq Llama 3 (Fallback)
   - Generates answers using the retrieved real-time context
""")

# 2. Pathway Integration: Connectors & xPack
pdf.chapter_title('2. Pathway Integration: Connectors & xPack')
pdf.chapter_body("""
1. Live Data Ingestion with Pathway Connectors:
   We utilize Pathway's real-time connector ecosystem to handle diverse data streams:
   - Custom Python Connectors (pw.io.python.read): We implemented a custom OPML connector that acts as an infinite stream of XML data, normalizing it on-the-fly.
   - API Connectors: Dedicated custom class connectors for NewsData.io and Twitter/X that treat API endpoints as continuous tables.

2. Streaming Transformations:
   All feature engineering happens in streaming mode:
   - Incremental Deduplication: Using pw.io.deduplicate to merge identical stories from different feeds.
   - Sliding Windows: Temporal windows group high-velocity news events to detect "breaking" clusters.

3. LLM Integration (LLM xPack):
   We leverage Pathway's LLM xPack to orchestrate the RAG pipeline:
   - Live Retrieval: The vector index is updated incrementally, allowing the LLM to query data milliseconds after ingestion.
   - Knowledge Graph: (Conceptual) The system builds a temporal graph of events to understand causality.
""")

# 3. Scalability & Extensibility
pdf.chapter_title('3. Scalability, Observability & Extension')
pdf.chapter_body("""
Scalability:
- Rust-Based Engine: Pathway handles high-throughput streams (thousands of events/sec) efficiently on a single node.
- Distributed Ready: Although running locally for the demo, Pathway pipelines can scale to clusters using Docker/Kubernetes without code changes.

Observability:
- Real-time logs track ingestion rates and LLM latency.
- "Global Pulse" UI visualizes the ingestion heartbeat.

Extension to Other Domains:
- Finance: Monitor stock tickers and news for algorithmic trading signals.
- Supply Chain: Track shipping disruptions and weather events in real-time.
- Cybersecurity: Analyze log streams for anomaly detection.
""")

# 4. Example Scenario
pdf.chapter_title('4. Example Scenario: "The Market Crash"')
pdf.chapter_body("""
Scenario:
A major tech company announces a surprise acquisition at 10:00 AM.

1. T+0s (Announcement): The press release hits a news wire.
2. T+2s (Ingestion): Our OPML ingestor detects the new item.
3. T+3s (Processing): Pathway normalizes the text and updates the vector index.
4. T+5s (User Query): User asks "What just happened with [Company]?"
5. T+6s (Answer): The system retrieves the article ingested 3 seconds ago and generates: "Breaking: [Company] just announced an acquisition of..."

Contrast with Traditional RAG:
A standard RAG system would wait for the nightly scrape (12-24 hours late), answering "I have no recent news on this."
""")

# 5. Demonstration Pipeline
pdf.chapter_title('5. Demonstration Pipeline')
pdf.chapter_body("""
The running demo illustrates:
1. "Global Pulse" Sidebar: Visualizing the raw stream of incoming news (updated every 5s via /pulse endpoint).
2. "Fetch Live" Button: Manually triggering a high-speed "Burst Mode" ingestion.
3. Chat Interface: Asking questions like "What is the latest on Apple?" and getting answers citing articles from 5 minutes ago.
4. Source Attribution: Every answer cites the specific RSS feed and timestamp, proving freshness.
""")

# 6. Testing & Evaluation
pdf.chapter_title('6. Testing & Evaluation')
pdf.chapter_body("""
Core validations performed:
1. Freshness Test: Verified that /pulse endpoint returns articles with timestamps < 5 minutes old.
2. Duplication Test: Confirmed that identical headlines from different sources are deduplicated.
3. Latency Test: Measured end-to-end time from "Ingest" to "Queryable" is < 2 seconds.
4. Load Test: Successfully handled ingestion of 1000+ feeds in "Burst Mode" without crashing.
""")

# 7. Team Presentation Summary
pdf.chapter_title('7. Team Presentation Summary')
pdf.chapter_body("""
Concept:
"Live Social Analyst" - A move from Static AI to Live AI.

Architecture:
A seamless pipeline: RSS/API -> Pathway Engine -> RAG -> Gemini.

Key Challenges:
- Ingesting noisy RSS feeds (solved with cleaning logic).
- Handling "Time": RSS feeds have inherent delays; we built a hybrid sorting mechanism to prioritize true publication time.
- Deduplication: Preventing the same AP/Reuters story appearing 50 times (solved with Pathway).

Why It Matters:
In a 24/7 world, static knowledge is a failure. This architecture proves that "Live AI" is accessible, scalable, and essential for decision-making.
""")

pdf.output("LiveSocialAnalyst_Report.pdf", "F")
print("✅ PDF Report Generated: LiveSocialAnalyst_Report.pdf")
