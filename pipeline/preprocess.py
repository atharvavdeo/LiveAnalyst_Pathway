import pathway as pw
from pipeline.reliability import calculate_reliability

def clean_text(text: str) -> str:
    # Remove newlines and excess whitespace
    if not text: return ""
    return text.replace("\n", " ").strip()

def preprocess(table: pw.Table) -> pw.Table:
    return table.select(
        text=pw.apply(clean_text, table.text),
        source=table.source,
        reliability=pw.apply(calculate_reliability, table.source),
        url=table.url
    )
