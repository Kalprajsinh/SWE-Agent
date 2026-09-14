import json
import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from agent import runner

router = APIRouter(prefix="/chat", tags=["chat"])


async def _sse_generator(user_message: str, repo: str = "", session_id: str = "default_session"):
    async for event in runner.graph_stream_run(user_message, repo=repo, session_id=session_id):
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

    session_id = body.get("session_id")
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        
    # Generate a title for the chat (e.g. first 30 chars of the message)
    title = user_message[:30] + "..." if len(user_message) > 30 else user_message
    
    from infrastructure.redis import add_user_session
    add_user_session(session.get("user")["login"], session_id, title)

    return StreamingResponse(
        _sse_generator(user_message, repo, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@router.get("/sessions")
async def list_sessions(request: Request):
    session = request.state.session
    user = session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    from infrastructure.redis import get_user_sessions
    sessions = get_user_sessions(user["login"])
    return {"sessions": sessions}

@router.get("/sessions/{session_id}")
async def get_session_history(request: Request, session_id: str):
    session = request.state.session
    if not session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    from infrastructure.redis import get_chat_history
    history = get_chat_history(session_id)
    return {"history": history}
