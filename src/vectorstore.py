import streamlit as st
import chromadb
from src.config import CHROMA_PERSIST_DIR, COLLECTION_NAME, RETRIEVER_K
from src.embeddings import get_embedding_function


@st.cache_resource
def get_vectorstore():
    """Load the pre-built ChromaDB collection from disk."""
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )
    return collection


def retrieve(query: str, k: int = RETRIEVER_K) -> list[dict]:
    """Retrieve the top-k most relevant document chunks for a query.

    Returns a list of dicts with keys: content, source, title, category, score.
    """
    collection = get_vectorstore()
    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    documents = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        # ChromaDB returns L2 distance by default; lower = more similar.
        # Convert to a 0-1 similarity score for display.
        similarity = 1 / (1 + distance)

        documents.append({
            "content": results["documents"][0][i],
            "source": results["metadatas"][0][i].get("source", "unknown"),
            "title": results["metadatas"][0][i].get("title", "Untitled"),
            "category": results["metadatas"][0][i].get("category", "General"),
            "score": round(similarity, 3),
        })

    return documents
