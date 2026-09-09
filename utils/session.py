import os
import json
from itsdangerous import URLSafeSerializer, BadSignature

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
_signer = URLSafeSerializer(SECRET_KEY, salt="session")

SESSION_COOKIE = "agent_session"


def load_session(request) -> dict:
    cookie = request.cookies.get(SESSION_COOKIE, "")
    if not cookie:
        return {}
    try:
        return _signer.loads(cookie)
    except BadSignature:
        return {}


def dump_session(session: dict) -> str:
    return _signer.dumps(session)


def set_session(response, session: dict):
    value = dump_session(session)
    response.set_cookie(
        SESSION_COOKIE,
        value,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7,  
    )


def clear_session(response):
    response.delete_cookie(SESSION_COOKIE)
