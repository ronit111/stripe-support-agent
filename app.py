import streamlit as st
import time
from src.chain import ask
from src.llm import get_provider_info
from src.config import SUGGESTED_QUESTIONS

# --- Page config ---
st.set_page_config(
    page_title="Stripe Support AI",
    page_icon="https://upload.wikimedia.org/wikipedia/commons/b/ba/Stripe_Logo%2C_revised_2016.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Hide default Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Top accent bar */
    .stApp {
        border-top: 3px solid #635BFF;
    }

    /* Chat message styling */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }

    /* Suggested question buttons */
    .suggested-btn button {
        background-color: #1A2742 !important;
        border: 1px solid #635BFF !important;
        color: #E8E8E8 !important;
        border-radius: 20px !important;
        padding: 0.4rem 1rem !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
    }
    .suggested-btn button:hover {
        background-color: #635BFF !important;
        color: white !important;
    }

    /* Source citation cards */
    .source-card {
        background-color: #1A2742;
        border: 1px solid #2A3752;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
    }
    .source-title {
        color: #635BFF;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .source-score {
        color: #888;
        font-size: 0.75rem;
    }
    .source-preview {
        color: #AAA;
        font-size: 0.8rem;
        margin-top: 0.25rem;
    }

    /* Metrics footer */
    .response-meta {
        color: #666;
        font-size: 0.75rem;
        margin-top: 0.5rem;
        padding-top: 0.25rem;
        border-top: 1px solid #1A2742;
    }
</style>
""", unsafe_allow_html=True)


# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []


# --- Sidebar ---
with st.sidebar:
    st.markdown("### Stripe Support AI")
    st.caption("AI-powered documentation assistant")

    st.divider()

    if st.button("New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # How it works
    st.markdown("#### How It Works")
    st.markdown("""
    1. Your question is matched against Stripe's documentation using semantic search
    2. The most relevant sections are retrieved from the vector database
    3. An LLM generates a precise answer grounded in the retrieved context
    """)

    st.divider()

    # Tech stack
    st.markdown("#### Tech Stack")
    provider = get_provider_info()
    st.markdown(f"""
    - **LLM**: {provider['provider']} ({provider['model']})
    - **Embeddings**: all-MiniLM-L6-v2 (ONNX)
    - **Vector DB**: ChromaDB
    - **Framework**: LangChain
    - **UI**: Streamlit
    """)

    st.divider()

    st.markdown(
        "[View on GitHub](https://github.com/ronitchidara/stripe-support-agent)",
        unsafe_allow_html=True,
    )


# --- Main content ---
st.markdown("# Stripe Support AI Agent")
st.caption("Ask me anything about Stripe's payments, subscriptions, refunds, and more. Answers are grounded in Stripe's official documentation with source citations.")


def handle_question(question: str):
    """Process a question through the RAG pipeline and display the response."""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    # Generate response
    with st.chat_message("assistant"):
        try:
            result = ask(question, st.session_state.messages[:-1])

            # Stream the response
            response_text = st.write_stream(result["answer"])
            total_time = time.time() - (time.time() - result["response_time"])

            # Source citations
            if result["sources"]:
                with st.expander(f"View Sources ({len(result['sources'])} documents)"):
                    for src in result["sources"]:
                        st.markdown(f"""
<div class="source-card">
    <span class="source-title">{src['title']}</span>
    <span class="source-score"> — relevance: {src['score']}</span>
    <div class="source-preview">{src['content'][:200]}...</div>
</div>
                        """, unsafe_allow_html=True)

            # Response metadata
            st.markdown(
                f'<div class="response-meta">Response time: {result["response_time"]:.1f}s · '
                f'{provider["provider"]} ({provider["model"]})</div>',
                unsafe_allow_html=True,
            )

            # Save to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "sources": result["sources"],
            })

        except Exception as e:
            error_msg = str(e)
            if "rate" in error_msg.lower() or "limit" in error_msg.lower():
                st.error("Rate limit reached. Please wait a moment and try again.")
            elif "api" in error_msg.lower() or "key" in error_msg.lower():
                st.error("LLM service unavailable. Please check the API configuration.")
            else:
                st.error(f"Something went wrong: {error_msg}")


# --- Suggested questions (shown when chat is empty) ---
if not st.session_state.messages:
    st.markdown("#### Try asking:")
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
            with st.expander(f"View Sources ({len(message['sources'])} documents)"):
                for src in message["sources"]:
                    st.markdown(f"""
<div class="source-card">
    <span class="source-title">{src['title']}</span>
    <span class="source-score"> — relevance: {src['score']}</span>
    <div class="source-preview">{src['content'][:200]}...</div>
</div>
                    """, unsafe_allow_html=True)

# --- Chat input ---
if prompt := st.chat_input("Ask about Stripe..."):
    handle_question(prompt)
    st.rerun()
