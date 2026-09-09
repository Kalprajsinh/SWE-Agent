from fastapi import APIRouter, Request, HTTPException
from agent.github_auth import list_repos

router = APIRouter(prefix="/repos", tags=["repos"])


@router.get("")
async def get_repos(request: Request):
    session = request.state.session
    if not session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = session.get("github_token", "")
    if not token:
        raise HTTPException(status_code=401, detail="No GitHub token in session")

    try:
        repos = list_repos(token)
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "full_name": r["full_name"],
                "description": r.get("description") or "",
                "language": r.get("language") or "Unknown",
                "stars": r.get("stargazers_count", 0),
                "private": r.get("private", False),
                "updated_at": r.get("updated_at", ""),
                "html_url": r.get("html_url", ""),
            }
            for r in repos
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repos: {e}")
