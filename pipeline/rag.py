# RAG query setup for Pathway

import pathway as pw
from pathway.xpacks.llm import answer_with_geometric_rag

def setup_rag_query(index, context_table):
    prompt = """
    You are a Real-Time Analyst. 
    Answer the user's question using the provided context.
    
    IMPORTANT:
    - You MUST state the 'reliability' of the information found in the context.
    - If context source is 'reddit', warn the user it is unverified.
    - If context source is 'news', confirm it is verified.
    """
    
    return answer_with_geometric_rag(
        index,
        strict_prompt=True,
        prompt_template=prompt,
        context_columns=["text", "source", "reliability"]
    )
