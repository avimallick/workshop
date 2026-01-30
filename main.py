import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from chain import MissingGroqApiKeyError, run_chat, run_chat_stream

app = FastAPI(title="Groq LangChain FastAPI", version="1.0.0")

if os.getenv("ALLOW_CORS", "").strip().lower() in {"1", "true", "yes"}:
    # Dev convenience for running a separate frontend on another origin (port/host).
    # If you use the built-in UI at "/", CORS isn't needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def ui() -> FileResponse:
    """Serve the single-file chat UI (same-origin; avoids CORS)."""
    index_path = Path(__file__).with_name("index.html")
    return FileResponse(index_path)


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


@app.post("/chat/stream")
def chat_stream(request: ChatRequest, x_api_key: Optional[str] = Header(default=None)) -> StreamingResponse:
    """Stream the model output as Server-Sent Events (SSE).

    Each event is a single line JSON payload: {"token": "..."}.
    The stream ends with: data: [DONE]
    """
    _require_api_key(x_api_key)

    def _event_stream():
        try:
            for token in run_chat_stream(request.message):
                payload = json.dumps({"token": token}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"
        except MissingGroqApiKeyError as exc:
            payload = json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"event: error\ndata: {payload}\n\n"
        except ValueError as exc:
            payload = json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"event: error\ndata: {payload}\n\n"
        except RuntimeError as exc:
            payload = json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"event: error\ndata: {payload}\n\n"

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
