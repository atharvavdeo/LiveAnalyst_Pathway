import pathway as pw
from pathway.stdlib.ml.index import KNNIndex
from pathway.stdlib.ml.embeddings import OpenAIEmbeddings

def build_index(table: pw.Table):
    # Uses OpenAI to turn text into vectors
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")

    return KNNIndex(
        table.text,
        table,
        n_dimensions=1536,
        embedder=embedder
    )
