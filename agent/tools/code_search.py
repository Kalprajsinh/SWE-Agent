import os
import subprocess
from agent.retrieval.repository_map import get_repository_map_formatted
from agent.retrieval.symbols import get_symbol_text
from agent.tools.filesystem import WORKSPACE_ROOT

def _get_repo_dir(repo: str) -> str:
    """Helper to get the absolute path for the repo."""
    safe_repo = repo.replace("/", "_")
    return os.path.join(WORKSPACE_ROOT, safe_repo)

def get_repository_map(repo: str) -> str:
    """
    Returns a high-level map of the repository's files and symbols.
    """
    repo_dir = _get_repo_dir(repo)
    if not os.path.exists(repo_dir):
        return f"Repository directory not found: {repo_dir}. Did you run clone_repo first?"
        
    return get_repository_map_formatted(repo_dir)


def get_symbol(repo: str, file_path: str, symbol: str) -> str:
    """
    Retrieve the exact source code for a specific symbol (class or function) from a file.
    `file_path` must be relative to the repository.
    """
    repo_dir = _get_repo_dir(repo)
    
    # Strip the leading `repo` prefix from file_path if it was provided
    safe_repo = repo.replace("/", "_")
    if file_path.startswith(f"{safe_repo}/"):
        file_path = file_path[len(safe_repo)+1:]
        
    return get_symbol_text(repo_dir, file_path, symbol)


def find_references(repo: str, symbol_name: str) -> str:
    """
    Performs a workspace-wide search for usages of a specific function or class name.
    """
    repo_dir = _get_repo_dir(repo)
    if not os.path.exists(repo_dir):
        return f"Repository directory not found."

    # Using rip-grep or standard grep style search via subprocess (since the agent runs this locally)
    # We use a simple python fallback search to avoid dependency on rg/grep being installed
    results = []
    
    for root, _, files in os.walk(repo_dir):
        if any(part.startswith('.') or part == 'node_modules' for part in os.path.split(root)):
            continue
            
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".md")):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, repo_dir).replace("\\", "/")
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if symbol_name in line:
                                results.append(f"{rel_path}:{i+1}: {line.strip()}")
                except Exception:
                    pass
                    
    if not results:
        return f"No references found for '{symbol_name}'."
        
    # Cap to 50 results to avoid massive context blowouts
    if len(results) > 50:
        return "\n".join(results[:50]) + f"\n... (and {len(results) - 50} more occurrences)"
        
    return "\n".join(results)
