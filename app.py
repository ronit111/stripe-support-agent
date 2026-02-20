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

# --- Custom CSS: Stripe-inspired light theme ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    /* Hide default Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Global typography */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Top accent bar — thin, elegant */
    .stApp {
        border-top: 3px solid #635BFF;
    }

    /* Main container breathing room */
    .stMainBlockContainer {
        max-width: 820px;
        padding-top: 2rem;
    }

    /* Hero title */
    .hero-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #0A2540;
        margin-bottom: 0;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        color: #425466;
        font-size: 1rem;
        margin-top: 0.5rem;
        margin-bottom: 2rem;
        line-height: 1.6;
    }

    /* Sidebar — clean light style */
    section[data-testid="stSidebar"] {
        background-color: #F6F9FC;
        border-right: 1px solid #E3E8EE;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] .stCaption {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 0.4rem;
    }
    .sidebar-brand-icon {
        width: 28px;
        height: 28px;
        background: #635BFF;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 0.85rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .sidebar-brand-text {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0A2540;
        letter-spacing: -0.01em;
    }
    .sidebar-badge {
        display: inline-block;
        background: #F0EEFF;
        color: #635BFF;
        border-radius: 10px;
        padding: 0.15rem 0.5rem;
        font-size: 0.6rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Chat messages */
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }

    /* Suggested question buttons — styled as clean cards */
    .stButton > button {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background: #FFFFFF !important;
        color: #0A2540 !important;
        border: 1px solid #E3E8EE !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        text-align: left !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }
    .stButton > button:hover {
        border-color: #635BFF !important;
        box-shadow: 0 2px 8px rgba(99, 91, 255, 0.1) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton > button {
        background: #FFFFFF !important;
        border: 1px solid #E3E8EE !important;
        color: #425466 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        border-color: #635BFF !important;
        color: #635BFF !important;
    }

    /* Source citation cards */
    .source-card {
        background: #FFFFFF;
        border: 1px solid #E3E8EE;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.6rem;
        transition: border-color 0.2s ease;
    }
    .source-card:hover {
        border-color: #635BFF;
    }
    .source-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.15rem;
    }
    .source-title {
        color: #0A2540;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .source-score {
        background: #F0EEFF;
        color: #635BFF;
        font-size: 0.68rem;
        padding: 0.12rem 0.45rem;
        border-radius: 8px;
        font-weight: 600;
    }
    .source-category {
        color: #635BFF;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.2rem;
    }
    .source-preview {
        color: #68778D;
        font-size: 0.78rem;
        line-height: 1.55;
        margin-top: 0.3rem;
    }

    /* Response metadata */
    .response-meta {
        display: flex;
        gap: 0.75rem;
        color: #8898AA;
        font-size: 0.72rem;
        margin-top: 0.75rem;
        padding-top: 0.5rem;
        border-top: 1px solid #E3E8EE;
    }
    .meta-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    .meta-dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: #635BFF;
        display: inline-block;
    }

    /* Tech stack pills in sidebar */
    .tech-pill {
        display: inline-block;
        background: #FFFFFF;
        border: 1px solid #E3E8EE;
        border-radius: 14px;
        padding: 0.18rem 0.55rem;
        font-size: 0.68rem;
        color: #425466;
        margin: 0.12rem;
        font-weight: 500;
    }

    /* How it works steps in sidebar */
    .step-container {
        display: flex;
        align-items: flex-start;
        gap: 0.65rem;
        margin-bottom: 0.65rem;
    }
    .step-num {
        background: #635BFF;
        color: #FFFFFF;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 700;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .step-text {
        color: #425466;
        font-size: 0.8rem;
        line-height: 1.45;
    }

    /* Chat input area */
    .stChatInput {
        border-color: #E3E8EE;
    }
    .stChatInput > div {
        border-color: #E3E8EE !important;
        border-radius: 10px !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-size: 0.85rem;
        font-weight: 600;
        color: #425466;
    }

    /* Dividers */
    hr {
        border-color: #E3E8EE !important;
    }

    /* Links */
    a {
        color: #635BFF !important;
        text-decoration: none !important;
    }
    a:hover {
        color: #0A2540 !important;
    }

    /* Scrollbar — subtle */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #F6F9FC;
    }
    ::-webkit-scrollbar-thumb {
        background: #D8DEE6;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #8898AA;
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
        <div class="sidebar-brand-icon">S</div>
        <span class="sidebar-brand-text">Stripe Support AI</span>
    </div>
    <span class="sidebar-badge">RAG-Powered</span>
    """, unsafe_allow_html=True)

    st.caption("AI documentation assistant grounded in Stripe's official docs")

    st.divider()

    if st.button("New Conversation", use_container_width=True):
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
    st.markdown("""
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
        "[View on GitHub](https://github.com/ronit111/stripe-support-agent)"
    )
    st.markdown(
        "[How It Works](How_It_Works)"
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
    with st.expander(f"View Sources ({len(sources)} documents)"):
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
                st.error("Rate limit reached. Please wait a moment and try again.")
            elif "api" in error_msg.lower() or "key" in error_msg.lower():
                st.error("LLM service unavailable. Check the API configuration.")
            else:
                st.error(f"Something went wrong: {error_msg}")


# --- Suggested questions (shown when chat is empty) ---
if not st.session_state.messages:
    st.markdown("##### Try asking")
    cols = st.columns(2)
    for i, q in enumerate(SUGGESTED_QUESTIONS):
        with cols[i % 2]:
            if st.button(q, key=f"suggest_{i}", use_container_width=True):
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
