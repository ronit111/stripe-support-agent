"""One-time script to embed Stripe docs into ChromaDB.

Run locally before deployment:
    python -m scripts.build_vectorstore

This creates the chroma_db/ directory with pre-computed embeddings.
Commit that directory to the repo so Streamlit Cloud loads from disk.
"""

import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import (
    CHROMA_PERSIST_DIR,
    STRIPE_DOCS_DIR,
    COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML-like frontmatter metadata from a markdown file."""
    metadata = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
            body = parts[2].strip()

    return metadata, body


def load_docs(docs_dir: str) -> list[dict]:
    """Load all markdown files from the docs directory."""
    docs = []
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(docs_dir, filename)
        with open(filepath, "r") as f:
            content = f.read()

        metadata, body = parse_frontmatter(content)
        metadata["source"] = filename
        metadata.setdefault("title", filename.replace(".md", "").replace("_", " ").title())
        metadata.setdefault("category", "General")

        docs.append({"content": body, "metadata": metadata})

    return docs


def chunk_docs(docs: list[dict]) -> list[dict]:
    """Split documents into chunks with metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )

    chunks = []
    for doc in docs:
        splits = splitter.split_text(doc["content"])
        for i, text in enumerate(splits):
            chunks.append({
                "id": f"{doc['metadata']['source']}_{i}",
                "content": text,
                "metadata": {
                    **doc["metadata"],
                    "chunk_index": i,
                },
            })

    return chunks


def build():
    """Build the ChromaDB vectorstore from Stripe docs."""
    print(f"Loading docs from {STRIPE_DOCS_DIR}...")
    docs = load_docs(STRIPE_DOCS_DIR)
    print(f"  Found {len(docs)} documents")

    print("Chunking documents...")
    chunks = chunk_docs(docs)
    print(f"  Created {len(chunks)} chunks")

    # Clear and recreate the collection
    print(f"Building vectorstore at {CHROMA_PERSIST_DIR}...")
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    # Delete existing collection if it exists
    try:
        client.delete_collection(COLLECTION_NAME)
    except ValueError:
        pass

    ef = DefaultEmbeddingFunction()
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )

    # Add chunks in batches
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["content"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        print(f"  Added batch {i // batch_size + 1}/{(len(chunks) - 1) // batch_size + 1}")

    print(f"\nDone! Collection '{COLLECTION_NAME}' has {collection.count()} chunks.")

    # Test query
    print("\nTest query: 'How do refunds work?'")
    results = collection.query(query_texts=["How do refunds work?"], n_results=3)
    for j, doc_id in enumerate(results["ids"][0]):
        source = results["metadatas"][0][j].get("source", "?")
        print(f"  {j+1}. {source} (distance: {results['distances'][0][j]:.4f})")


if __name__ == "__main__":
    build()
