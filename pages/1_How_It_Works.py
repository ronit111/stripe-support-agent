import streamlit as st
from src.llm import get_provider_info

st.set_page_config(
    page_title="How It Works — Stripe Support AI",
    page_icon="💳",
    layout="wide",
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        border-top: 3px solid transparent;
        border-image: linear-gradient(90deg, #635BFF, #80E9FF, #635BFF) 1;
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #635BFF, #80E9FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
    }

    .arch-diagram {
        background: rgba(26, 39, 66, 0.5);
        border: 1px solid rgba(99, 91, 255, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        line-height: 1.6;
        overflow-x: auto;
    }

    .pipeline-card {
        background: linear-gradient(135deg, rgba(26, 39, 66, 0.8), rgba(26, 39, 66, 0.5));
        border: 1px solid rgba(99, 91, 255, 0.15);
        border-radius: 12px;
        padding: 1.5rem;
        height: 100%;
        transition: border-color 0.2s ease;
    }
    .pipeline-card:hover {
        border-color: rgba(99, 91, 255, 0.4);
    }
    .pipeline-num {
        background: linear-gradient(135deg, #635BFF, #80E9FF);
        color: #0A1628;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.9rem;
        margin-bottom: 0.75rem;
    }
    .pipeline-title {
        color: #E8E8E8;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .pipeline-desc {
        color: #8892A6;
        font-size: 0.88rem;
        line-height: 1.6;
    }

    .tech-row {
        display: flex;
        align-items: center;
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(99, 91, 255, 0.08);
    }
    .tech-row:last-child {
        border-bottom: none;
    }
    .tech-name {
        color: #635BFF;
        font-weight: 600;
        font-size: 0.9rem;
        width: 200px;
        flex-shrink: 0;
    }
    .tech-detail {
        color: #C0C8D8;
        font-size: 0.85rem;
        flex: 1;
    }
    .tech-why {
        color: #8892A6;
        font-size: 0.8rem;
        flex: 1;
        font-style: italic;
    }

    .decision-card {
        background: rgba(26, 39, 66, 0.4);
        border-left: 3px solid #635BFF;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }
    .decision-title {
        color: #E8E8E8;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.35rem;
    }
    .decision-desc {
        color: #8892A6;
        font-size: 0.85rem;
        line-height: 1.6;
    }

    .cta-section {
        background: linear-gradient(135deg, rgba(99, 91, 255, 0.12), rgba(128, 233, 255, 0.06));
        border: 1px solid rgba(99, 91, 255, 0.25);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin-top: 1rem;
    }
    .cta-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #E8E8E8;
        margin-bottom: 0.5rem;
    }
    .cta-desc {
        color: #8892A6;
        font-size: 0.95rem;
        max-width: 600px;
        margin: 0 auto 1.5rem auto;
        line-height: 1.6;
    }

    .stat-box {
        text-align: center;
        padding: 1rem;
    }
    .stat-num {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #635BFF, #80E9FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .stat-label {
        color: #8892A6;
        font-size: 0.8rem;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("# How It Works")
st.caption("A look under the hood at the RAG (Retrieval Augmented Generation) pipeline powering this assistant.")

# --- Stats row ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="stat-box"><div class="stat-num">25</div><div class="stat-label">Stripe Doc Pages</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="stat-box"><div class="stat-num">345</div><div class="stat-label">Embedded Chunks</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="stat-box"><div class="stat-num">&lt;2s</div><div class="stat-label">Response Time</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="stat-box"><div class="stat-num">$0</div><div class="stat-label">Running Cost</div></div>', unsafe_allow_html=True)

st.divider()

# --- Architecture ---
st.markdown('<div class="section-title">Architecture</div>', unsafe_allow_html=True)

st.markdown("""
<div class="arch-diagram">
<pre style="color: #C0C8D8; margin: 0;">
  User Question
       │
       ▼
  ┌─────────────────────────────────────────────────┐
  │              <span style="color: #635BFF; font-weight: 600;">Streamlit UI</span>                       │
  │         (Chat Interface + Source Display)        │
  └──────────────────────┬──────────────────────────┘
                         │
                         ▼
  ┌─────────────────────────────────────────────────┐
  │           <span style="color: #635BFF; font-weight: 600;">LangChain RAG Pipeline</span>                │
  │                                                 │
  │  ┌──────────────┐     ┌──────────────────────┐  │
  │  │  <span style="color: #80E9FF;">ChromaDB</span>     │     │  <span style="color: #80E9FF;">Groq API</span>            │  │
  │  │  Vector Store │────▶│  Llama 3.3 70B       │  │
  │  │  (345 chunks) │     │  (streaming)          │  │
  │  └──────┬───────┘     └──────────┬───────────┘  │
  │         │                        │               │
  │    Top 4 chunks            Grounded answer       │
  └─────────┴────────────────────────┴───────────────┘
                         │
                         ▼
              Response + Source Citations
</pre>
</div>
""", unsafe_allow_html=True)

st.divider()

# --- Pipeline Steps ---
st.markdown('<div class="section-title">The RAG Pipeline</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
<div class="pipeline-card">
    <div class="pipeline-num">1</div>
    <div class="pipeline-title">Retrieve</div>
    <div class="pipeline-desc">
        Your question is converted into a vector embedding using the all-MiniLM-L6-v2 model (ONNX runtime).
        This embedding is compared against pre-computed embeddings of Stripe's documentation stored in ChromaDB.
        The top 4 most semantically similar document chunks are retrieved, each with a relevance score.
    </div>
</div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
<div class="pipeline-card">
    <div class="pipeline-num">2</div>
    <div class="pipeline-title">Augment</div>
    <div class="pipeline-desc">
        Retrieved document chunks are injected into a carefully designed prompt template alongside your
        question and conversation history. The prompt instructs the LLM to answer <strong>only</strong>
        based on the provided context, preventing hallucination and ensuring accuracy.
    </div>
</div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
<div class="pipeline-card">
    <div class="pipeline-num">3</div>
    <div class="pipeline-title">Generate</div>
    <div class="pipeline-desc">
        The augmented prompt is sent to the LLM, which generates a response grounded in the retrieved
        documentation. Responses are streamed in real-time for a responsive experience.
        Source citations are attached so you can verify every answer.
    </div>
</div>
    """, unsafe_allow_html=True)

st.divider()

# --- Tech Stack ---
st.markdown('<div class="section-title">Tech Stack</div>', unsafe_allow_html=True)

provider = get_provider_info()

tech_items = [
    ("LLM", f"{provider['provider']} ({provider['model']})", "Fastest free-tier inference — sub-second token generation"),
    ("Embeddings", "all-MiniLM-L6-v2 (ONNX)", "Lightweight (~80MB), runs on CPU, no GPU required"),
    ("Vector Database", "ChromaDB (persistent)", "Zero infrastructure, pre-computed embeddings load from disk"),
    ("Framework", "LangChain", "Industry-standard RAG orchestration with provider flexibility"),
    ("UI", "Streamlit", "Clean chat interface with custom dark theme"),
    ("Knowledge Base", "25 curated Stripe pages", "Covers payments, billing, disputes, webhooks, and more"),
]

for name, detail, why in tech_items:
    st.markdown(f"""
<div class="tech-row">
    <span class="tech-name">{name}</span>
    <span class="tech-detail">{detail}</span>
    <span class="tech-why">{why}</span>
</div>
    """, unsafe_allow_html=True)

st.divider()

# --- Key Design Decisions ---
st.markdown('<div class="section-title">Key Design Decisions</div>', unsafe_allow_html=True)

decisions = [
    (
        "Pre-computed Embeddings",
        "Document embeddings are generated once during the build step and committed to the repository. "
        "The deployed app loads them from disk, eliminating runtime embedding computation. "
        "This cuts cold start time and keeps memory usage well under Streamlit Cloud's 1GB limit."
    ),
    (
        "Swappable LLM Provider",
        "The LLM integration is abstracted behind a factory function. Switching from Groq to OpenAI "
        "or Google Gemini requires changing a single environment variable — no code changes. "
        "This demonstrates production-grade vendor flexibility."
    ),
    (
        "Conversation Memory",
        "The last 5 exchanges are maintained in the prompt context, enabling natural follow-up questions. "
        "Memory is scoped to the browser session and resets on page refresh."
    ),
    (
        "Score-based Retrieval",
        "Retrieved documents include relevance scores shown to the user, giving full transparency "
        "into how confident the system is about each source."
    ),
]

for title, desc in decisions:
    st.markdown(f"""
<div class="decision-card">
    <div class="decision-title">{title}</div>
    <div class="decision-desc">{desc}</div>
</div>
    """, unsafe_allow_html=True)

st.divider()

# --- CTA ---
st.markdown("""
<div class="cta-section">
    <div class="cta-title">Want Something Like This for Your Business?</div>
    <div class="cta-desc">
        I build AI-powered tools that work in production — customer support agents,
        document Q&A systems, and custom AI workflows. Architected for your scale and budget.
    </div>
</div>
""", unsafe_allow_html=True)

st.link_button(
    "Hire me on Upwork",
    "https://www.upwork.com/freelancers/ronitchidara",
    use_container_width=True,
)
