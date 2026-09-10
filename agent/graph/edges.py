from agent.graph.state import AgentState
from agent.runner import _parse_tool_call


def route_after_llm(state: AgentState) -> str:
    last_msg = state["messages"][-1]["content"]
    if _parse_tool_call(last_msg):
        return "tool_node"
    return "decide_node"


def route_after_decide(state: AgentState) -> str:
    if state.get("done"):
        return "END"
    return "llm_node"
