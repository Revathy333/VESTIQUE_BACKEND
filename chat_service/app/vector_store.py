# import os
# import chromadb
# from sentence_transformers import SentenceTransformer

# CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
# CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

# # ---------------------------------------------------------------------------
# # Lazy singletons — initialised once on first use, not at import time.
# # This prevents the container from crashing before ChromaDB / HF hub are ready.
# # ---------------------------------------------------------------------------
# _client = None
# _collection = None
# _embedder = None


# def _get_embedder() -> SentenceTransformer:
#     global _embedder
#     if _embedder is None:
#         _embedder = SentenceTransformer("all-MiniLM-L6-v2")
#     return _embedder


# def _get_collection():
#     global _client, _collection
#     if _collection is None:
#         _client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
#         _collection = _client.get_or_create_collection(
#             "vestique_knowledge",
#             metadata={"hnsw:space": "cosine"},   # cosine similarity
#         )
#     return _collection


# # ---------------------------------------------------------------------------
# # Public API
# # ---------------------------------------------------------------------------

# def add_knowledge(doc_id: str, text: str) -> None:
#     """Embed and store a single document. Safe to call multiple times (upsert)."""
#     embedding = _get_embedder().encode(text).tolist()
#     _get_collection().upsert(          # upsert = add or overwrite
#         ids=[doc_id],
#         embeddings=[embedding],
#         documents=[text],
#     )


# def search_knowledge(query: str, n_results: int = 3) -> list[str]:
#     """Return the top-n most relevant documents for *query*."""
#     embedding = _get_embedder().encode(query).tolist()
#     results = _get_collection().query(
#         query_embeddings=[embedding],
#         n_results=n_results,
#     )
#     return results["documents"][0] if results.get("documents") else []


# def collection_count() -> int:
#     """Handy helper to check how many docs are stored."""
#     return _get_collection().count()

# def search_knowledge_by_prefix(query: str, prefix: str, n_results: int = 3) -> list[str]:
#     """
#     Semantic search restricted to documents whose ID starts with a given prefix.
#     e.g. prefix='profile_review' only searches profile review documents.
#     """
#     embedding = _get_embedder().encode(query).tolist()
#     collection = _get_collection()

#     # Get total count of docs matching this prefix
#     all_ids = collection.get(where_document=None)["ids"] if False else None

#     try:
#         results = collection.query(
#             query_embeddings=[embedding],
#             n_results=n_results,
#             where={"$contains": prefix} if False else None,  # ChromaDB filters by metadata, not ID
#         )
#         # Filter results by ID prefix after retrieval
#         docs = []
#         ids = results.get("ids", [[]])[0]
#         documents = results.get("documents", [[]])[0]
#         for doc_id, doc in zip(ids, documents):
#             if doc_id.startswith(prefix):
#                 docs.append(doc)
#         return docs
#     except Exception:
#         return []


import os
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

_client = None
_embedder = None
_collections = {}

COLLECTION_NAMES = ["faq", "creators", "profile_reviews", "general_reviews", "posts"]


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    return _client


def _get_collection(name: str):
    global _collections
    if name not in _collections:
        _collections[name] = _get_client().get_or_create_collection(
            name, metadata={"hnsw:space": "cosine"}
        )
    return _collections[name]


def add_knowledge(doc_id: str, text: str) -> None:
    """Legacy — adds to 'faq' collection. Used by knowledge_base.py."""
    embedding = _get_embedder().encode(text).tolist()
    _get_collection("faq").upsert(ids=[doc_id], embeddings=[embedding], documents=[text])


def add_to_collection(collection_name: str, doc_id: str, text: str) -> None:
    """Add a document to a specific named collection."""
    embedding = _get_embedder().encode(text).tolist()
    _get_collection(collection_name).upsert(
        ids=[doc_id], embeddings=[embedding], documents=[text]
    )


def search_collection(collection_name: str, query: str, n_results: int = 3) -> list[str]:
    """Semantic search within a specific collection."""
    embedding = _get_embedder().encode(query).tolist()
    collection = _get_collection(collection_name)
    if collection.count() == 0:
        return []
    results = collection.query(query_embeddings=[embedding], n_results=min(n_results, collection.count()))
    return results["documents"][0] if results.get("documents") else []


def search_knowledge(query: str, n_results: int = 5) -> list[str]:
    """Legacy — searches 'faq' collection only."""
    return search_collection("faq", query, n_results)


def collection_count() -> int:
    return _get_collection("faq").count()