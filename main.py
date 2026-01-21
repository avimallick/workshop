import os
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from chain import MissingGroqApiKeyError, run_chat

app = FastAPI(title="Groq LangChain FastAPI", version="1.0.0")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _require_api_key(x_api_key: Optional[str]) -> None:
    service_key = os.getenv("SERVICE_API_KEY", "").strip()
    if not service_key:
        return
    if not x_api_key or x_api_key != service_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-KEY")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, x_api_key: Optional[str] = Header(default=None)) -> ChatResponse:
    _require_api_key(x_api_key)

    try:
        answer = run_chat(request.message)
    except MissingGroqApiKeyError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(answer=answer)
