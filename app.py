import streamlit as st
import time
from src.chain import ask
from src.llm import get_provider_info
from src.config import SUGGESTED_QUESTIONS

# --- Page config ---
st.set_page_config(
    page_title="Stripe Support AI",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

provider = get_provider_info()

# --- Custom CSS ---
st.markdown("""
<style>
    /* Hide default Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Top gradient accent bar */
    .stApp {
        border-top: 3px solid transparent;
        border-image: linear-gradient(90deg, #635BFF, #80E9FF, #635BFF) 1;
    }

    /* Hero title gradient */
    .hero-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #635BFF 0%, #80E9FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0;
        line-height: 1.2;
    }
    .hero-subtitle {
        color: #8892A6;
        font-size: 0.95rem;
        margin-top: 0.25rem;
        margin-bottom: 1.5rem;
    }

    /* Sidebar branding */
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .sidebar-brand-text {
        font-size: 1.1rem;
        font-weight: 700;
        background: linear-gradient(135deg, #635BFF, #80E9FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .sidebar-badge {
        display: inline-block;
        background: rgba(99, 91, 255, 0.15);
        color: #635BFF;
        border: 1px solid rgba(99, 91, 255, 0.3);
        border-radius: 12px;
        padding: 0.15rem 0.5rem;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Chat container improvements */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }

    /* Suggested question cards */
    .question-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.75rem;
        margin: 1rem 0 2rem 0;
    }
    .question-card {
        background: linear-gradient(135deg, rgba(99, 91, 255, 0.08), rgba(128, 233, 255, 0.05));
        border: 1px solid rgba(99, 91, 255, 0.2);
        border-radius: 12px;
        padding: 1rem;
        cursor: pointer;
        transition: all 0.25s ease;
        text-decoration: none;
    }
    .question-card:hover {
        border-color: #635BFF;
        background: linear-gradient(135deg, rgba(99, 91, 255, 0.15), rgba(128, 233, 255, 0.08));
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 91, 255, 0.15);
    }
    .question-card-icon {
        font-size: 1.25rem;
        margin-bottom: 0.5rem;
    }
    .question-card-text {
        color: #E8E8E8;
        font-size: 0.88rem;
        line-height: 1.4;
    }

    /* Source citation cards */
    .source-card {
        background: linear-gradient(135deg, rgba(26, 39, 66, 0.8), rgba(26, 39, 66, 0.6));
        border: 1px solid rgba(99, 91, 255, 0.15);
        border-left: 3px solid #635BFF;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        transition: border-color 0.2s ease;
    }
    .source-card:hover {
        border-left-color: #80E9FF;
    }
    .source-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.25rem;
    }
    .source-title {
        color: #635BFF;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .source-score {
        background: rgba(99, 91, 255, 0.12);
        color: #A8A3FF;
        font-size: 0.7rem;
        padding: 0.1rem 0.4rem;
        border-radius: 8px;
        font-weight: 500;
    }
    .source-category {
        color: #80E9FF;
        font-size: 0.7rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.25rem;
    }
    .source-preview {
        color: #8892A6;
        font-size: 0.78rem;
        line-height: 1.5;
        margin-top: 0.35rem;
    }

    /* Response metadata */
    .response-meta {
        display: flex;
        gap: 1rem;
        color: #556;
        font-size: 0.72rem;
        margin-top: 0.75rem;
        padding-top: 0.5rem;
        border-top: 1px solid rgba(99, 91, 255, 0.1);
    }
    .meta-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    .meta-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #635BFF;
        display: inline-block;
    }

    /* Tech stack pills in sidebar */
    .tech-pill {
        display: inline-block;
        background: rgba(99, 91, 255, 0.1);
        border: 1px solid rgba(99, 91, 255, 0.2);
        border-radius: 16px;
        padding: 0.2rem 0.6rem;
        font-size: 0.72rem;
        color: #A8A3FF;
        margin: 0.15rem;
        font-weight: 500;
    }

    /* How it works steps */
    .step-container {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
    }
    .step-num {
        background: linear-gradient(135deg, #635BFF, #80E9FF);
        color: #0A1628;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 700;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .step-text {
        color: #C0C8D8;
        font-size: 0.82rem;
        line-height: 1.4;
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 2rem 1rem;
    }
    .empty-icon {
        font-size: 3rem;
        margin-bottom: 0.75rem;
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0A1628;
    }
    ::-webkit-scrollbar-thumb {
        background: #2A3752;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #635BFF;
    }
</style>
""", unsafe_allow_html=True)


# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []


# --- Sidebar ---
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <span style="font-size: 1.5rem;">💳</span>
        <span class="sidebar-brand-text">Stripe Support AI</span>
    </div>
    <span class="sidebar-badge">RAG-Powered</span>
    """, unsafe_allow_html=True)

    st.caption("AI documentation assistant grounded in Stripe's official docs")

    st.divider()

    if st.button("🔄  New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # How it works
    st.markdown("**How It Works**")
    st.markdown("""
    <div class="step-container">
        <div class="step-num">1</div>
        <div class="step-text">Your question is embedded and matched against Stripe docs via semantic search</div>
    </div>
    <div class="step-container">
        <div class="step-num">2</div>
        <div class="step-text">Top 4 most relevant documentation sections are retrieved from ChromaDB</div>
    </div>
    <div class="step-container">
        <div class="step-num">3</div>
        <div class="step-text">LLM generates an answer grounded strictly in the retrieved context</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Tech stack
    st.markdown("**Tech Stack**")
    st.markdown(f"""
    <div style="margin: 0.5rem 0;">
        <span class="tech-pill">Groq</span>
        <span class="tech-pill">Llama 3.3 70B</span>
        <span class="tech-pill">LangChain</span>
        <span class="tech-pill">ChromaDB</span>
        <span class="tech-pill">all-MiniLM-L6-v2</span>
        <span class="tech-pill">Streamlit</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown(
        "[📂 View on GitHub](https://github.com/ronit111/stripe-support-agent)"
    )
    st.markdown(
        "[🏗️ How It Works →](How_It_Works)"
    )


# --- Main content ---
st.markdown('<div class="hero-title">Stripe Support AI Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Ask anything about Stripe — payments, subscriptions, refunds, webhooks, and more. '
    'Every answer is grounded in official documentation with source citations.</div>',
    unsafe_allow_html=True,
)


def render_sources(sources: list[dict]):
    """Render source citation cards."""
    with st.expander(f"📄 View Sources ({len(sources)} documents)"):
        for src in sources:
            preview = src["content"][:180].replace("\n", " ")
            st.markdown(f"""
<div class="source-card">
    <div class="source-category">{src['category']}</div>
    <div class="source-header">
        <span class="source-title">{src['title']}</span>
        <span class="source-score">{src['score']:.0%} match</span>
    </div>
    <div class="source-preview">{preview}...</div>
</div>
            """, unsafe_allow_html=True)


def render_response_meta(response_time: float):
    """Render response metadata footer."""
    st.markdown(f"""
<div class="response-meta">
    <span class="meta-item"><span class="meta-dot"></span> {response_time:.1f}s</span>
    <span class="meta-item">{provider['provider']}</span>
    <span class="meta-item">{provider['model']}</span>
</div>
    """, unsafe_allow_html=True)


def handle_question(question: str):
    """Process a question through the RAG pipeline and display the response."""
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            result = ask(question, st.session_state.messages[:-1])
            response_text = st.write_stream(result["answer"])
            total_time = time.time() - result["start_time"]

            if result["sources"]:
                render_sources(result["sources"])
            render_response_meta(total_time)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "sources": result["sources"],
                "response_time": total_time,
            })

        except Exception as e:
            error_msg = str(e)
            if "rate" in error_msg.lower() or "limit" in error_msg.lower():
                st.error("⏳ Rate limit reached. Please wait a moment and try again.")
            elif "api" in error_msg.lower() or "key" in error_msg.lower():
                st.error("🔑 LLM service unavailable. Check the API configuration.")
            else:
                st.error(f"Something went wrong: {error_msg}")


# --- Suggested questions (shown when chat is empty) ---
if not st.session_state.messages:
    question_icons = ["💰", "⚡", "🔄", "🔔", "🔀", "🚨"]

    st.markdown("#### Try asking:")
    cols = st.columns(2)
    for i, q in enumerate(SUGGESTED_QUESTIONS):
        icon = question_icons[i] if i < len(question_icons) else "💬"
        with cols[i % 2]:
            if st.button(f"{icon}  {q}", key=f"suggest_{i}", use_container_width=True):
                handle_question(q)
                st.rerun()

# --- Chat history ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            render_sources(message["sources"])
        if message.get("response_time"):
            render_response_meta(message["response_time"])

# --- Chat input ---
if prompt := st.chat_input("Ask about Stripe..."):
    handle_question(prompt)
    st.rerun()
