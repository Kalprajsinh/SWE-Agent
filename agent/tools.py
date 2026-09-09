import os
import subprocess
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).parent.parent / "workspace"
WORKSPACE_ROOT.mkdir(exist_ok=True)

GITHUB_PAT = os.getenv("GITHUB_PAT", "")

def _run_shell(cmd: str, cwd: Optional[str] = None, timeout: int = 300) -> str:
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        if result.returncode != 0:
            output = f"[exit code {result.returncode}]\n" + output
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except Exception as e:
        return f"Error running command: {e}"

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


def list_files(directory: str = "") -> str:

    base = WORKSPACE_ROOT / directory if directory else WORKSPACE_ROOT
    if not base.exists():
        return f"Directory does not exist: {base}"
    
    lines = []
    for p in sorted(base.rglob("*")):
        if any(part.startswith(".") or part in ("node_modules", "__pycache__", ".git") for part in p.parts):
            continue
        rel = p.relative_to(WORKSPACE_ROOT)
        prefix = "📁 " if p.is_dir() else "📄 "
        lines.append(f"{prefix}{rel}")
    
    return "\n".join(lines) if lines else "(empty directory)"


def read_file(file_path: str) -> str:

    full_path = WORKSPACE_ROOT / file_path
    if not full_path.exists():
        return f"File not found: {full_path}"
    try:
        content = full_path.read_text(encoding="utf-8")
        if len(content) > 8000:
            content = content[:8000] + f"\n... [truncated, {len(content)} chars total]"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(file_path: str, content: str) -> str:
    if file_path.endswith("/") or file_path.endswith("\\"):
        return f"Error: file_path must be a file, not a directory. Got: {file_path}"
        
    full_path = WORKSPACE_ROOT / file_path
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} bytes to {full_path}"
    except Exception as e:
        return f"Error writing file: {e}"


def run_command(cmd: str, repo_dir: str = "", timeout: int = 600) -> str:
    cwd = str(WORKSPACE_ROOT / repo_dir) if repo_dir else str(WORKSPACE_ROOT)
    return _run_shell(cmd, cwd=cwd, timeout=timeout)


def create_pr(owner: str, repo: str, branch_name: str, commit_message: str, pr_title: str, pr_body: str = "") -> str:
    pat = os.getenv("GITHUB_PAT", GITHUB_PAT)
    if not pat:
        return "Error: GITHUB_PAT is not set."

    repo_dir = str(WORKSPACE_ROOT / f"{owner}_{repo}")
    if not Path(repo_dir).exists():
        return f"Repo not found in workspace. Run clone_repo first."

    _run_shell('git config user.email "agent@coverage-bot.local"', cwd=repo_dir)
    _run_shell('git config user.name "Coverage Agent"', cwd=repo_dir)

    branch_res = _run_shell(f"git checkout -b {branch_name}", cwd=repo_dir)

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

TOOLS = {
    "clone_repo": {
        "fn": clone_repo,
        "description": "Clone a GitHub repository into the local workspace. If already cloned, pulls latest.",
        "parameters": {
            "owner": "GitHub username or org name",
            "repo": "Repository name",
        },
    },
    "list_files": {
        "fn": list_files,
        "description": "List all files in a workspace directory recursively.",
        "parameters": {
            "directory": "Relative path within workspace (leave empty to list all)",
        },
    },
    "read_file": {
        "fn": read_file,
        "description": "Read the content of a file in the workspace.",
        "parameters": {
            "file_path": "Path relative to workspace root",
        },
    },
    "write_file": {
        "fn": write_file,
        "description": "Write or create a file in the workspace.",
        "parameters": {
            "file_path": "Path relative to workspace root",
            "content": "Full file content to write",
        },
    },
    "run_command": {
        "fn": run_command,
        "description": "Run a shell command in a workspace directory (for tests, install, coverage, etc.).",
        "parameters": {
            "cmd": "Shell command to run",
            "repo_dir": "Relative path within workspace (e.g. 'owner_repo')",
        },
    },
    "create_pr": {
        "fn": create_pr,
        "description": "Commit all changes, push a new branch, and open a Pull Request on GitHub.",
        "parameters": {
            "owner": "GitHub owner/org",
            "repo": "Repository name",
            "branch_name": "New branch name (e.g. 'coverage/add-tests')",
            "commit_message": "Git commit message",
            "pr_title": "Pull Request title",
            "pr_body": "Pull Request description (optional)",
        },
    },
}
