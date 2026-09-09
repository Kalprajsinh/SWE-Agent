import os
import httpx
from urllib.parse import urlencode

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
OAUTH_CALLBACK_URL = "http://localhost:8080/auth/callback"

GITHUB_API = "https://api.github.com"


def oauth_enabled() -> bool:
    return bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)


def get_oauth_url(state: str = "") -> str:
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": OAUTH_CALLBACK_URL,
        "scope": "repo user",
        "state": state,
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"


def exchange_code(code: str) -> str:
    with httpx.Client(timeout=15.0) as client:
        r = client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": OAUTH_CALLBACK_URL,
            },
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()
        return r.json().get("access_token", "")


def get_user(token: str) -> dict:
    with httpx.Client(timeout=15.0) as client:
        r = client.get(
            f"{GITHUB_API}/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        r.raise_for_status()
        return r.json()


def list_repos(token: str, per_page: int = 50) -> list[dict]:
    repos = []
    page = 1
    with httpx.Client(timeout=15.0) as client:
        while True:
            r = client.get(
                f"{GITHUB_API}/user/repos",
                params={
                    "sort": "updated",
                    "per_page": per_page,
                    "page": page,
                    "affiliation": "owner,collaborator",
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
    return repos


def validate_pat(pat: str) -> dict | None:
    try:
        return get_user(pat)
    except Exception:
        return None
