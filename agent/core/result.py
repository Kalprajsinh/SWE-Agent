from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class ToolResult:
    tool_name: str
    args: dict
    output: str
    success: bool
    error: Optional[str] = None

    @classmethod
    def ok(cls, tool_name: str, args: dict, output: str) -> "ToolResult":
        return cls(tool_name=tool_name, args=args, output=output, success=True)

    @classmethod
    def fail(cls, tool_name: str, args: dict, error: str) -> "ToolResult":
        return cls(tool_name=tool_name, args=args, output=error, success=False, error=error)
