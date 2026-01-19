# Vector Store for Semantic Search using ChromaDB

import time
from typing import List, Dict, Optional
import threading

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("⚠️ ChromaDB not installed. Vector search disabled.")

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ sentence-transformers not installed. Using fallback search.")


class VectorStore:
    """
    Lightweight vector store for semantic search on live news data.
    Uses ChromaDB for storage and sentence-transformers for embeddings.
    """
    
    def __init__(self, collection_name: str = "live_news"):
        self._lock = threading.Lock()
        self._item_hashes = set()  # Track unique items
        
        if CHROMA_AVAILABLE:
            # In-memory ChromaDB (no persistence needed for live data)
            self.client = chromadb.Client(Settings(anonymized_telemetry=False))
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print("✅ ChromaDB initialized (in-memory)")
        else:
            self.client = None
            self.collection = None
            
        if EMBEDDINGS_AVAILABLE:
            # Load lightweight embedding model
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Embedding model loaded (all-MiniLM-L6-v2)")
        else:
            self.embedder = None
    
    def _hash_item(self, item: Dict) -> str:
        """Create unique hash for an item."""
        return f"{item.get('source', '')}_{item.get('text', '')[:50]}_{item.get('url', '')}"
    
    def add_items(self, items: List[Dict]) -> int:
        """
        Add items to the vector store.
        Returns number of new items added.
        """
        if not CHROMA_AVAILABLE or not EMBEDDINGS_AVAILABLE:
            return 0
            
        new_items = []
        with self._lock:
            for item in items:
                item_hash = self._hash_item(item)
                if item_hash not in self._item_hashes:
                    self._item_hashes.add(item_hash)
                    new_items.append(item)
        
        if not new_items:
            return 0
            
        # Prepare data for ChromaDB
        ids = [f"item_{hash(self._hash_item(item)) % 10**9}" for item in new_items]
        documents = [item.get('text', '')[:500] for item in new_items]  # Limit text length
        metadatas = []
        
        for item in new_items:
            # Parse created_utc - handle both ISO strings and Unix timestamps
            created = item.get('created_utc', 0)
            if isinstance(created, str):
                try:
                    # ISO format: 2026-01-10T07:57:09Z
                    from datetime import datetime
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    created = dt.timestamp()
                except:
                    created = time.time()
            else:
                try:
                    created = float(created)
                except:
                    created = time.time()
            
            metadatas.append({
                "source": item.get('source', 'unknown'),
                "url": item.get('url', ''),
                "created_utc": created,
                "reliability": item.get('reliability', 'Unknown')
            })
        
        # Generate embeddings
        embeddings = self.embedder.encode(documents).tolist()
        
        # Add to collection
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        except Exception as e:
            # Handle duplicate ID errors gracefully
            pass
            
        return len(new_items)
    
    def search(self, query: str, n_results: int = 20) -> List[Dict]:
        """
        Search for semantically similar items - NO TIME LIMIT for true real-time RAG.
        Searches ALL indexed content.
        
        Args:
            query: Search query
            n_results: Max number of results
            
        Returns:
            List of matching items with scores
        """
        if not CHROMA_AVAILABLE or not EMBEDDINGS_AVAILABLE:
            return []
            
        if self.collection.count() == 0:
            return []
            
        # Generate query embedding
        query_embedding = self.embedder.encode([query]).tolist()[0]
        
        # Search ALL content - NO TIME FILTER
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, self.collection.count())
            )
        
        # Format results
        items = []
        if results and results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0][:n_results]):
                meta = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0
                items.append({
                    'text': doc,
                    'source': meta.get('source', 'unknown'),
                    'url': meta.get('url', ''),
                    'created_utc': meta.get('created_utc', 0),
                    'reliability': meta.get('reliability', 'Unknown'),
                    'similarity_score': 1 - distance  # Convert distance to similarity
                })
                
        return items
    
    def get_fresh_items(self, max_age_seconds: int = 300) -> List[Dict]:
        """Get all items newer than max_age_seconds."""
        if not CHROMA_AVAILABLE:
            return []
            
        cutoff_time = time.time() - max_age_seconds
        
        try:
            results = self.collection.get(
                where={"created_utc": {"$gte": cutoff_time}}
            )
            
            items = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    meta = results['metadatas'][i] if results['metadatas'] else {}
                    items.append({
                        'text': doc,
                        'source': meta.get('source', 'unknown'),
                        'url': meta.get('url', ''),
                        'created_utc': meta.get('created_utc', 0),
                        'reliability': meta.get('reliability', 'Unknown')
                    })
            return items
        except Exception:
            return []
    
    def count(self) -> int:
        """Return total items in store."""
        if self.collection:
            return self.collection.count()
        return 0


# Global instance
_vector_store: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
