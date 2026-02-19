import time
from langchain_core.messages import HumanMessage, AIMessage
from src.llm import get_llm
from src.vectorstore import retrieve
from src.prompts import SYSTEM_TEMPLATE


def format_context(docs: list[dict]) -> str:
    """Format retrieved documents into a context string for the LLM."""
    parts = []
    for i, doc in enumerate(docs, 1):
        parts.append(f"[Source {i}: {doc['title']}]\n{doc['content']}")
    return "\n\n---\n\n".join(parts)


def format_chat_history(messages: list[dict]) -> list:
    """Convert session state messages to LangChain message objects."""
    history = []
    for msg in messages:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history.append(AIMessage(content=msg["content"]))
    return history


def ask(question: str, chat_history: list[dict] | None = None) -> dict:
    """Run the full RAG pipeline: retrieve → format → generate.

    Returns a dict with keys: answer (str generator for streaming),
    sources (list of retrieved docs), response_time (float).
    """
    start = time.time()

    # 1. Retrieve relevant chunks
    sources = retrieve(question)

    # 2. Build the prompt with context
    context = format_context(sources)
    history = format_chat_history(chat_history or [])

    messages = [
        ("system", SYSTEM_TEMPLATE.format(context=context)),
        *[
            ("human" if isinstance(m, HumanMessage) else "assistant", m.content)
            for m in history[-10:]  # Keep last 5 exchanges (10 messages)
        ],
        ("human", question),
    ]

    # 3. Stream the response from the LLM
    llm = get_llm()

    def stream_response():
        for chunk in llm.stream(messages):
            if chunk.content:
                yield chunk.content

    return {
        "answer": stream_response(),
        "sources": sources,
        "response_time": time.time() - start,
    }
