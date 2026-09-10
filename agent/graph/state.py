from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    messages: Annotated[list[dict], operator.add]
    task: str
    repo: str
    steps: int
    final_answer: str
    done: bool
    last_tool: str
