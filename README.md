# Stripe Support AI Agent

An AI-powered customer support assistant that answers questions about Stripe using Retrieval Augmented Generation (RAG). Every response is grounded in Stripe's official documentation with source citations — no hallucination, no guessing.

**[Try the live demo →](https://stripe-support-agent.streamlit.app)**

---

## What It Does

- **Answers Stripe questions accurately** — retrieves relevant documentation sections and generates grounded responses
- **Cites its sources** — every answer includes expandable source citations with relevance scores
- **Streams responses in real-time** — sub-2-second time to first token via Groq inference

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  User        │────▶│  Semantic Search  │────▶│  LLM Generation │
│  Question    │     │  (ChromaDB)       │     │  (Groq + Llama) │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │                          │
                    Retrieves top 4              Generates answer
                    relevant chunks              grounded in context
                           │                          │
                    ┌──────▼──────┐            ┌──────▼──────┐
                    │ Stripe Docs  │            │  Response +  │
                    │ (25 pages)   │            │  Citations   │
                    └─────────────┘            └─────────────┘
```

**How it works:**
1. Your question is converted into a vector embedding
2. ChromaDB finds the most semantically similar documentation chunks
3. Retrieved chunks are injected as context into the LLM prompt
4. The LLM generates an answer grounded strictly in the provided documentation
5. Source citations are displayed so you can verify every answer

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| **LLM** | Groq (Llama 3.3 70B) | Fastest free-tier inference — sub-second token generation |
| **Embeddings** | all-MiniLM-L6-v2 (ONNX) | Lightweight (~80MB), runs on CPU, no GPU needed |
| **Vector DB** | ChromaDB | Zero infrastructure, pre-computed embeddings load from disk |
| **Framework** | LangChain | Industry-standard RAG orchestration |
| **UI** | Streamlit | Clean chat interface with custom dark theme |
| **Knowledge Base** | 25 curated Stripe doc pages | Covers payments, billing, disputes, webhooks, and more |

## Swap LLM Provider

The LLM integration is abstracted behind a factory function. Switching providers requires changing a single environment variable:

| Provider | Env Var | Model |
|---|---|---|
| **Groq** (default) | `GROQ_API_KEY` | llama-3.3-70b-versatile |
| OpenAI | `OPENAI_API_KEY` | gpt-4o-mini |
| Google | `GOOGLE_API_KEY` | gemini-2.0-flash |

```bash
# Switch to OpenAI
LLM_PROVIDER=openai OPENAI_API_KEY=sk-... streamlit run app.py
```

No code changes needed.

## Run Locally

```bash
# Clone
git clone https://github.com/ronit111/stripe-support-agent.git
cd stripe-support-agent

# Install dependencies
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (free at console.groq.com)

# Run
streamlit run app.py
```

The app loads pre-computed embeddings from the `chroma_db/` directory — no additional setup needed.

### Rebuild the Vector Store (optional)

If you modify the documentation files in `data/stripe_docs/`:

```bash
python -m scripts.build_vectorstore
```

This re-embeds all documents and updates the `chroma_db/` directory.

## Project Structure

```
├── app.py                      # Streamlit chat interface
├── pages/
│   └── 1_How_It_Works.py      # Architecture explainer page
├── src/
│   ├── config.py               # Settings + provider configs
│   ├── embeddings.py           # ONNX embedding model (cached)
│   ├── vectorstore.py          # ChromaDB retrieval
│   ├── llm.py                  # LLM provider factory
│   ├── chain.py                # RAG pipeline assembly
│   └── prompts.py              # System prompt templates
├── data/stripe_docs/           # 25 curated Stripe doc pages
├── scripts/
│   └── build_vectorstore.py    # Embedding pipeline
├── chroma_db/                  # Pre-computed vector store
└── .streamlit/config.toml      # Custom dark theme
```

## Key Design Decisions

**Pre-computed embeddings**: Document embeddings are generated once and committed to the repo. The deployed app loads them from disk, cutting cold start time from ~30s to ~5s.

**ChromaDB's ONNX runtime**: Uses the lightweight ONNX embedding function instead of full sentence-transformers, keeping memory under 500MB — critical for Streamlit Cloud's 1GB limit.

**Conversation memory**: Last 5 exchanges are maintained in context, enabling natural follow-up questions without blowing up token usage.

**Graceful degradation**: Rate limits, API failures, and off-topic questions are all handled with user-friendly messages instead of stack traces.

---

Built by [Ronit Chidara](https://www.upwork.com/freelancers/ronitchidara)
