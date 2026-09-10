import os
from pathlib import Path
from agent.tools.shell import _run_shell

WORKSPACE_ROOT = Path(__file__).parent.parent.parent / "workspace"
WORKSPACE_ROOT.mkdir(exist_ok=True)

GITHUB_PAT = os.getenv("GITHUB_PAT", "")


def clone_repo(owner: str, repo: str) -> str:
    pat = os.getenv("GITHUB_PAT", GITHUB_PAT)
    if not pat:
        return "Error: GITHUB_PAT is not set."

    target = WORKSPACE_ROOT / f"{owner}_{repo}"
    repo_url = f"https://oauth2:{pat}@github.com/{owner}/{repo}.git"

    if target.exists():
        result = _run_shell("git pull", cwd=str(target))
        return f"Repo already cloned. Pulled latest:\n{result}"
    else:
        result = _run_shell(f'git clone "{repo_url}" "{target}"')
        return f"Cloned {owner}/{repo} into {target}:\n{result}"
