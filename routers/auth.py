
import os
import secrets
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

from agent.github_auth import (
    oauth_enabled, get_oauth_url, exchange_code, get_user, validate_pat
)
from utils.session import set_session, clear_session

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/status")
async def auth_status(request: Request):
    session = request.state.session
    if session.get("user"):
        return {"authenticated": True, "user": session["user"], "oauth": session.get("oauth", False)}
    return {"authenticated": False}


@router.get("/login")
async def login(request: Request):
    if oauth_enabled():
        state = secrets.token_urlsafe(16)
        request.state.session["oauth_state"] = state
        url = get_oauth_url(state)
        return RedirectResponse(url)
    return JSONResponse({"mode": "pat", "message": "OAuth not configured. Use /auth/pat-login."})


@router.get("/callback")
async def oauth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    if error:
        return RedirectResponse(f"/?error={error}")

    expected_state = request.state.session.get("oauth_state", "")
    if state != expected_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token = exchange_code(code)
    if not token:
        raise HTTPException(status_code=400, detail="Failed to exchange OAuth code")

    user = get_user(token)
    request.state.session["user"] = {
        "login": user["login"],
        "name": user.get("name") or user["login"],
        "avatar_url": user.get("avatar_url", ""),
    }
    request.state.session["github_token"] = token
    request.state.session["oauth"] = True

    return RedirectResponse("/?auth=success")


@router.post("/pat-login")
async def pat_login(request: Request):
    body = await request.json()
    pat = body.get("pat", "").strip()
    if not pat:
        raise HTTPException(status_code=400, detail="PAT is required")

    user = validate_pat(pat)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid PAT or GitHub API error")

    request.state.session["user"] = {
        "login": user["login"],
        "name": user.get("name") or user["login"],
        "avatar_url": user.get("avatar_url", ""),
    }
    request.state.session["github_token"] = pat
    request.state.session["oauth"] = False

    return {"ok": True, "user": request.state.session["user"]}


@router.post("/logout")
async def logout(request: Request, response: Response):
    request.state.session.clear()
    return {"ok": True}
