import json
import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from agent import runner

router = APIRouter(prefix="/chat", tags=["chat"])


async def _sse_generator(user_message: str, repo: str = ""):
    async for event in runner.graph_stream_run(user_message, repo=repo):
        payload = json.dumps(event)
        yield f"data: {payload}\n\n"
    yield "data: [DONE]\n\n"


@router.post("")
async def chat(request: Request):
    session = request.state.session
    if not session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    body = await request.json()
    user_message = body.get("message", "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="message is required")

    repo = body.get("repo", "")

    return StreamingResponse(
        _sse_generator(user_message, repo),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
