from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class RunState:
    repository: str          
    task: str       
    run_id: str             
    started_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "running"  
    steps: int = 0
    pr_url: Optional[str] = None
    error: Optional[str] = None

    def mark_done(self, pr_url: str = ""):
        self.status = "completed"
        if pr_url:
            self.pr_url = pr_url

    def mark_failed(self, error: str):
        self.status = "failed"
        self.error = error
