import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from agent.tools.shell import _run_shell

WORKSPACE_ROOT = Path(__file__).parent.parent.parent / "workspace"
GITHUB_PAT = os.getenv("GITHUB_PAT", "")


def create_pr(
    owner: str,
    repo: str,
    branch_name: str,
    commit_message: str,
    pr_title: str,
    pr_body: str = "",
) -> str:
    pat = os.getenv("GITHUB_PAT", GITHUB_PAT)
    if not pat:
        return "Error: GITHUB_PAT is not set."

    repo_dir = str(WORKSPACE_ROOT / f"{owner}_{repo}")
    if not os.path.exists(repo_dir):
        return "Repo not found in workspace. Run clone_repo first."

    _run_shell('git config user.email "agent@coverage-bot.local"', cwd=repo_dir)
    _run_shell('git config user.name "Coverage Agent"', cwd=repo_dir)

    _run_shell(f"git checkout -b {branch_name}", cwd=repo_dir)
    _run_shell("git add -A", cwd=repo_dir)

    commit_res = _run_shell(f'git commit -m "{commit_message}"', cwd=repo_dir)
    if "nothing to commit" in commit_res:
        return "Nothing to commit — no changes detected."

    authed_url = f"https://{pat}@github.com/{owner}/{repo}.git"
    _run_shell(f"git remote set-url origin {authed_url}", cwd=repo_dir)
    push_res = _run_shell(f"git push -u origin {branch_name}", cwd=repo_dir)
    clean_url = f"https://github.com/{owner}/{repo}.git"
    _run_shell(f"git remote set-url origin {clean_url}", cwd=repo_dir)

    if "error" in push_res.lower() and "already exists" not in push_res:
        return f"Push failed:\n{push_res}"

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = json.dumps({
        "title": pr_title,
        "body": pr_body or f"Automated PR by Coverage Agent\n\n{commit_message}",
        "head": branch_name,
        "base": "main",
    }).encode("utf-8")

    try:
        req = urllib.request.Request(api_url, data=payload, method="POST")
        req.add_header("Authorization", f"token {pat}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pr_url = data.get("html_url", "unknown")
            return f"✅ Pull Request created successfully!\n🔗 {pr_url}"
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        return f"GitHub API error ({e.code}): {err}"
    except Exception as e:
        return f"Error creating PR: {e}"
