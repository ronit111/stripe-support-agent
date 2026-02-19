import streamlit as st
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


@st.cache_resource
def get_embedding_function():
    """Load ChromaDB's default ONNX embedding function (all-MiniLM-L6-v2).

    Uses ONNX runtime instead of full sentence-transformers, keeping memory
    footprint under ~100MB — critical for Streamlit Cloud's 1GB limit.
    """
    return DefaultEmbeddingFunction()
