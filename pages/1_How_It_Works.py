import streamlit as st
from src.llm import get_provider_info

st.set_page_config(
    page_title="How It Works — Stripe Support AI",
    page_icon="https://upload.wikimedia.org/wikipedia/commons/b/ba/Stripe_Logo%2C_revised_2016.svg",
    layout="wide",
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { border-top: 3px solid #635BFF; }
</style>
""", unsafe_allow_html=True)

st.markdown("# How It Works")
st.caption("A look under the hood at the RAG (Retrieval Augmented Generation) pipeline powering this assistant.")

st.divider()

# --- Architecture Overview ---
st.markdown("## Architecture")

st.markdown("""
```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Your        │────▶│  Semantic Search  │────▶│  LLM Generation │
│  Question    │     │  (ChromaDB)       │     │  (Groq + Llama) │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │                          │
                    Retrieves top 4              Generates answer
                    relevant chunks              grounded in context
                           │                          │
                    ┌──────▼──────┐            ┌──────▼──────┐
                    │ Stripe Docs  │            │  Response +  │
                    │ (25 pages,   │            │  Source       │
                    │  embedded)   │            │  Citations    │
                    └─────────────┘            └─────────────┘
```
""")

st.divider()

# --- Pipeline Steps ---
st.markdown("## The RAG Pipeline")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 1. Retrieve")
    st.markdown("""
    When you ask a question, it's converted into a vector embedding using the
    `all-MiniLM-L6-v2` model. This embedding is compared against pre-computed
    embeddings of Stripe's documentation stored in ChromaDB.

    The top 4 most semantically similar document chunks are retrieved, each
    with a relevance score.
    """)

with col2:
    st.markdown("### 2. Augment")
    st.markdown("""
    The retrieved document chunks are injected into a carefully designed prompt
    template alongside your question and conversation history.

    The prompt instructs the LLM to answer **only** based on the provided context,
    preventing hallucination and ensuring accuracy.
    """)

with col3:
    st.markdown("### 3. Generate")
    st.markdown("""
    The augmented prompt is sent to the LLM, which generates a response
    grounded in the retrieved documentation. Responses are streamed in
    real-time for a responsive experience.

    Source citations are attached so you can verify every answer.
    """)

st.divider()

# --- Tech Stack ---
st.markdown("## Tech Stack")

provider = get_provider_info()

tech_data = {
    "Component": ["LLM", "Embeddings", "Vector Database", "Framework", "UI", "Knowledge Base"],
    "Technology": [
        f"{provider['provider']} ({provider['model']})",
        "all-MiniLM-L6-v2 (ONNX Runtime)",
        "ChromaDB (persistent, pre-computed)",
        "LangChain",
        "Streamlit",
        "Stripe Documentation (25 curated pages)",
    ],
    "Why": [
        "Fastest inference available on free tier — sub-second token generation",
        "Lightweight (~80MB), runs on CPU, no GPU required",
        "Zero infrastructure, loads from disk, no server needed",
        "Industry-standard RAG orchestration with provider flexibility",
        "Rapid prototyping with professional theming",
        "Universally recognized, well-structured, real-world use case",
    ],
}

st.table(tech_data)

st.divider()

# --- Key Design Decisions ---
st.markdown("## Key Design Decisions")

st.markdown("""
**Pre-computed embeddings**: Document embeddings are generated once during the build step
and committed to the repository. The deployed app loads them from disk, eliminating the need
to run the embedding model during cold start. This cuts startup time and memory usage significantly.

**Swappable LLM provider**: The LLM integration is abstracted behind a factory function.
Switching from Groq to OpenAI or Google Gemini requires changing a single environment variable —
no code changes needed. This demonstrates production-grade vendor flexibility.

**Conversation memory**: The last 5 exchanges are maintained in the prompt context, allowing
follow-up questions to work naturally. Memory is scoped to the session and resets on page refresh.

**Score-based retrieval**: Retrieved documents include relevance scores, giving transparency
into how confident the system is about each source. Low-confidence retrievals are filtered out
to prevent the LLM from working with irrelevant context.
""")

st.divider()

# --- CTA ---
st.markdown("## Want Something Like This for Your Business?")
st.markdown("""
This demo was built by **Ronit Chidara** — I help businesses implement AI-powered tools
that actually work in production.

Whether you need a customer support agent, document Q&A system, or custom AI workflow,
I can build it with the right architecture for your scale and budget.
""")
st.link_button(
    "Hire me on Upwork",
    "https://www.upwork.com/freelancers/ronitchidara",
    use_container_width=True,
)
