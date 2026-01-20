# Main Pathway application combining all data streams

import pathway as pw
import os
from dotenv import load_dotenv

from ingest.x_stream import x_table
from ingest.news_api import news_table
from pipeline.preprocess import preprocess
from pipeline.vector_index import build_index
from pipeline.rag import setup_rag_query

load_dotenv()

x_clean = x_table.select(source=pw.this.source, text=pw.this.text, url=pw.this.url, created_utc=pw.cast(str, pw.this.created_utc))
combined_stream = pw.concat(news_table, x_clean)

processed_data = preprocess(combined_stream)

index = build_index(processed_data)

rag_app = setup_rag_query(index, processed_data)

host = "0.0.0.0"
port = 8000
print(f"🚀 Live Analyst running at http://{host}:{port}")

pw.io.http.write_json(rag_app, host=host, port=port)
pw.run()
