import os
import inspect
from typing import Final
from typing import Iterator

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


def run_chat_stream(message: str) -> Iterator[str]:
    """Stream a chat completion using Groq via LangChain.

    Yields small text chunks as they are generated.
    """
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

    # Be defensive about the ChatGroq constructor: different versions may (or may not)
    # accept "streaming=True". We'll only pass it if supported.
    llm_kwargs: dict = {"model": model, "temperature": temperature, "api_key": api_key}
    try:
        sig = inspect.signature(ChatGroq)
        if "streaming" in sig.parameters:
            llm_kwargs["streaming"] = True
    except Exception:
        # If signature inspection fails, just proceed without streaming kwarg.
        pass

    try:
        llm = ChatGroq(**llm_kwargs)
        chain = prompt | llm

        for chunk in chain.stream({"message": message}):
            # Typically an AIMessageChunk with .content being the incremental token(s).
            text = getattr(chunk, "content", None)
            if isinstance(text, str) and text:
                yield text
            elif isinstance(chunk, str) and chunk:
                yield chunk
    except Exception as exc:  # LangChain or Groq errors bubble up here
        raise RuntimeError(f"Groq model call failed: {exc}") from exc
