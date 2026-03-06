import os
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

# ---------------------------------------------------------------------------
# Lazy singletons — initialised once on first use, not at import time.
# This prevents the container from crashing before ChromaDB / HF hub are ready.
# ---------------------------------------------------------------------------
_client = None
_collection = None
_embedder = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        _collection = _client.get_or_create_collection(
            "vestique_knowledge",
            metadata={"hnsw:space": "cosine"},   # cosine similarity
        )
    return _collection


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_knowledge(doc_id: str, text: str) -> None:
    """Embed and store a single document. Safe to call multiple times (upsert)."""
    embedding = _get_embedder().encode(text).tolist()
    _get_collection().upsert(          # upsert = add or overwrite
        ids=[doc_id],
        embeddings=[embedding],
        documents=[text],
    )


def search_knowledge(query: str, n_results: int = 3) -> list[str]:
    """Return the top-n most relevant documents for *query*."""
    embedding = _get_embedder().encode(query).tolist()
    results = _get_collection().query(
        query_embeddings=[embedding],
        n_results=n_results,
    )
    return results["documents"][0] if results.get("documents") else []


def collection_count() -> int:
    """Handy helper to check how many docs are stored."""
    return _get_collection().count()