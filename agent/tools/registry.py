from agent.tools.filesystem import list_files, read_file, write_file
from agent.tools.git import clone_repo
from agent.tools.shell import run_command
from agent.tools.github import create_pr
from agent.tools.code_search import get_repository_map, get_symbol, find_references

TOOLS = {
    "clone_repo": {
        "fn": clone_repo,
        "description": "Clone a GitHub repository into the local workspace. If already cloned, pulls latest.",
        "parameters": {
            "owner": "GitHub username or org name",
            "repo": "Repository name",
        },
    },
    "get_repository_map": {
        "fn": get_repository_map,
        "description": "Get a structural map of all files and symbols (classes/functions) in the repository.",
        "parameters": {
            "repo": "Repository directory name (e.g. 'owner_repo')",
        },
    },
    "get_symbol": {
        "fn": get_symbol,
        "description": "Retrieve the source code of a specific class or function instead of reading an entire file.",
        "parameters": {
            "repo": "Repository directory name",
            "file_path": "Path to the file relative to repo root",
            "symbol": "Name of the class or function",
        },
    },
    "find_references": {
        "fn": find_references,
        "description": "Find usages of a specific function or class across the entire repository.",
        "parameters": {
            "repo": "Repository directory name",
            "symbol_name": "Name of the symbol to search for",
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
