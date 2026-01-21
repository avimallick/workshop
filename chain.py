import os
from typing import Final

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from prompts import SYSTEM_PROMPT


class MissingGroqApiKeyError(ValueError):
    """Raised when GROQ_API_KEY is not set."""


def _get_env_float(name: str, default: float) -> float:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {name} value: {value}") from exc


def run_chat(message: str) -> str:
    """Run a chat completion using Groq via LangChain."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise MissingGroqApiKeyError("GROQ_API_KEY environment variable is required.")

    model: Final[str] = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
    temperature = _get_env_float("GROQ_TEMPERATURE", 0.7)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("user", "{message}"),
        ]
    )

    try:
        llm = ChatGroq(model=model, temperature=temperature, api_key=api_key)
        chain = prompt | llm
        response = chain.invoke({"message": message})
        return response.content
    except Exception as exc:  # LangChain or Groq errors bubble up here
        raise RuntimeError(f"Groq model call failed: {exc}") from exc
