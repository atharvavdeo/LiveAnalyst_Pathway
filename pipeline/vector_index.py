# Vector indexing for semantic search

import pathway as pw
from pathway.stdlib.ml.index import KNNIndex
from pathway.stdlib.ml.embeddings import OpenAIEmbeddings

def build_index(table: pw.Table):
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")

    return KNNIndex(
        table.text,
        table,
        n_dimensions=1536,
        embedder=embedder
    )
