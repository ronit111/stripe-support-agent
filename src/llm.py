import os
import importlib
import streamlit as st
from src.config import LLM_PROVIDER, PROVIDER_CONFIGS, LLM_TEMPERATURE, LLM_MAX_TOKENS


@st.cache_resource
def get_llm():
    """Create the LLM client based on the configured provider.

    Provider is selected via LLM_PROVIDER env var. Swapping from Groq to
    OpenAI or Google is a single env var change — no code modifications needed.
    """
    config = PROVIDER_CONFIGS.get(LLM_PROVIDER)
    if not config:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}. Choose from: {list(PROVIDER_CONFIGS.keys())}")

    api_key = os.getenv(config["env_var"])
    if not api_key:
        raise ValueError(f"Missing API key. Set {config['env_var']} in your environment or .env file.")

    module = importlib.import_module(config["module"])
    llm_class = getattr(module, config["class_name"])

    return llm_class(
        model=config["model"],
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        streaming=True,
    )


def get_provider_info() -> dict:
    """Return display info about the current LLM provider."""
    config = PROVIDER_CONFIGS.get(LLM_PROVIDER, {})
    return {
        "provider": LLM_PROVIDER.capitalize(),
        "model": config.get("model", "unknown"),
    }
