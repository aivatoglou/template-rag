"""FastAPI entry point for the Agent."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from src.models import APIRequest, APIResponse
from src.agent import build_agent
from src.db.store import count_docs

_agent = None

# Initialize the agent at server startup to eliminate first-request latency.
# While the agent creation is lightweight, pre-loading it is best practice.
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent
    _agent = build_agent()
    yield


app = FastAPI(title="RAG Agent Assistant", lifespan=lifespan)


@app.post("/query", response_model=APIResponse)
def query(req: APIRequest) -> APIResponse:
    try:
        result = _agent.run(req.message)

        response_text = result.content
        reasoning_text = result.reasoning_content or ""
        model_name = result.model or ""
        tools_list = [t.tool_name for t in (result.tools or []) if hasattr(t, "tool_name")]

        m = result.metrics
        total_tokens = getattr(m, "total_tokens", 0) or 0
        input_tokens = getattr(m, "input_tokens", 0) or 0
        output_tokens = getattr(m, "output_tokens", 0) or 0
        reasoning_tokens = getattr(m, "reasoning_tokens", 0) or 0
        duration_ms = int((getattr(m, "duration", 0.0) or 0.0) * 1000)

        return APIResponse(
            response=response_text.answer,
            sources=response_text.sources,
            reasoning=reasoning_text,
            model_id=model_name,
            duration_ms=duration_ms,
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            tools_used=tools_list,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "total_chunks": count_docs()}
