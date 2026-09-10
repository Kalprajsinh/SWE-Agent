import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from routers.auth import router as auth_router
from routers.repos import router as repos_router
from routers.chat import router as chat_router
from utils.session import load_session, dump_session, SESSION_COOKIE
from agent import llm

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Coverage Agent starting...")
    if llm.is_available():
        print(f"[OK] Qwen LLM ready: {os.getenv('QWEN_MODEL', 'qwen3-max')}")
    else:
        print(f"[WARN] Qwen API not reachable. Check QWEN_API_KEY in .env")
    yield
    print("[INFO] Shutting down.")


app = FastAPI(
    title="Coverage Agent",
    description="A from-scratch coding agent that improves test coverage via GitHub + Ollama.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def session_middleware(request: Request, call_next):
    session = load_session(request)
    request.state.session = session

    response = await call_next(request)

    new_value = dump_session(request.state.session)
    old_value = request.cookies.get(SESSION_COOKIE, "")
    if new_value != old_value:
        response.set_cookie(
            SESSION_COOKIE,
            new_value,
            httponly=True,
            samesite="lax",
            max_age=86400 * 7,
        )

    return response


app.include_router(auth_router)
app.include_router(repos_router)
app.include_router(chat_router)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "llm_available": llm.is_available(),
        "model": os.getenv("QWEN_MODEL", "qwen3-max"),
        "provider": "Alibaba Cloud DashScope",
        "thinking": os.getenv("ENABLE_THINKING", "true"),
    }


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        log_level="info",
    )
