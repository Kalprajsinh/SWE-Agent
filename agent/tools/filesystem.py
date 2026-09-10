from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent.parent / "workspace"
WORKSPACE_ROOT.mkdir(exist_ok=True)


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
