import os
from dotenv import load_dotenv

load_dotenv()

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

PROVIDER_CONFIGS = {
    "groq": {
        "module": "langchain_groq",
        "class_name": "ChatGroq",
        "model": "llama-3.3-70b-versatile",
        "env_var": "GROQ_API_KEY",
    },
    "openai": {
        "module": "langchain_openai",
        "class_name": "ChatOpenAI",
        "model": "gpt-4o-mini",
        "env_var": "OPENAI_API_KEY",
    },
    "google": {
        "module": "langchain_google_genai",
        "class_name": "ChatGoogleGenerativeAI",
        "model": "gemini-2.0-flash",
        "env_var": "GOOGLE_API_KEY",
    },
}

# LLM parameters
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 1024

# Retrieval parameters
RETRIEVER_K = 4
SIMILARITY_THRESHOLD = 0.3

# Paths
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
STRIPE_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "stripe_docs")

# Chunking parameters (used by build script)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Collection name
COLLECTION_NAME = "stripe_docs"

# Suggested questions for the UI
SUGGESTED_QUESTIONS = [
    "How do I set up recurring subscriptions?",
    "What happens when a payment dispute is filed?",
    "How do I process refunds via the API?",
    "Explain Stripe webhook event types",
    "What's the difference between PaymentIntents and Charges?",
    "How do I handle failed payments?",
]
