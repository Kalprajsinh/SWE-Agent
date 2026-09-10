from agent.tools.filesystem import list_files, read_file, write_file
from agent.tools.git import clone_repo
from agent.tools.shell import run_command
from agent.tools.github import create_pr

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
