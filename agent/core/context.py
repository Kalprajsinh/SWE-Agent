import uuid
from dataclasses import dataclass
from pathlib import Path

WORKERFOLDER = Path(__file__).parent.parent.parent.parent / "workerfolder"

@dataclass
class RunContext:
    run_id: str
    workspace_root: Path   
    repo_dir: Path     
    github_pat: str

    def safe_path(self, relative: str) -> Path:
        resolved = (self.workspace_root / relative).resolve()
        if not str(resolved).startswith(str(self.workspace_root.resolve())):
            raise ValueError(f"Path escape blocked: {relative!r}")
        return resolved

def create_run_context(github_pat: str) -> RunContext:
    run_id = uuid.uuid4().hex[:8]
    workspace_root = WORKERFOLDER / "runs" / run_id
    repo_dir = workspace_root / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    return RunContext(
        run_id=run_id,
        workspace_root=workspace_root,
        repo_dir=repo_dir,
        github_pat=github_pat,
    )
