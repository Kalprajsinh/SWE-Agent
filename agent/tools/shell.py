import subprocess
import platform
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).parent.parent.parent / "workspace"


def _normalize_cmd(cmd: str) -> str:
    if platform.system() != "Windows":
        return cmd
    if cmd.strip().startswith("cat "):
        return "type " + cmd.strip()[4:]
    return cmd


def _run_shell(cmd: str, cwd: Optional[str] = None, timeout: int = 600) -> str:
    cmd = _normalize_cmd(cmd)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout or ""
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr or ''}"
        if result.returncode != 0:
            output = f"[exit code {result.returncode}]\n" + output
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except Exception as e:
        return f"Error running command: {e}"


def run_command(cmd: str, repo_dir: str = "", timeout: int = 600) -> str:
    cwd = str(WORKSPACE_ROOT / repo_dir) if repo_dir else str(WORKSPACE_ROOT)
    return _run_shell(cmd, cwd=cwd, timeout=timeout)
