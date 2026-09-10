import json
import re
from langsmith import traceable
from agent import llm as llm_module
from agent.graph.state import AgentState
from agent.tools.registry import TOOLS

from agent.runner import _build_system_prompt, _parse_tool_call, _is_hallucinating

MAX_STEPS = 35
TOOL_CALL_PATTERN = re.compile(r"<TOOL_CALL>\s*(\{.*?\})\s*</TOOL_CALL>", re.DOTALL)


@traceable(run_type="llm", name="llm_node")
def llm_node(state: AgentState) -> dict:
    messages = state["messages"]
    response = llm_module.chat(messages)
    return {
        "messages": [{"role": "assistant", "content": response}],
        "steps": state["steps"] + 1,
    }


@traceable(run_type="tool", name="tool_node")
def tool_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1]["content"]
    tool_call = _parse_tool_call(last_msg)

    if not tool_call:
        return {
            "messages": [],
            "done": True,
            "final_answer": TOOL_CALL_PATTERN.sub("", last_msg).strip(),
            "last_tool": "",
        }

    tool_name = tool_call.get("tool", "")
    args = tool_call.get("args", {})

    if tool_name not in TOOLS:
        result = f"Unknown tool: '{tool_name}'. Available: {', '.join(TOOLS.keys())}"
    else:
        try:
            result = TOOLS[tool_name]["fn"](**args)
        except TypeError as e:
            result = f"Tool call error (wrong args?): {e}"
        except Exception as e:
            result = f"Tool execution error: {e}"

    tool_result_msg = f"<TOOL_RESULT>\n{result}\n</TOOL_RESULT>"
    return {
        "messages": [{"role": "user", "content": tool_result_msg}],
        "last_tool": tool_name,
    }


def decide_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1]["content"]
    steps = state["steps"]

    if steps >= MAX_STEPS:
        return {
            "done": True,
            "final_answer": "Max steps reached. The agent did not produce a final answer.",
            "messages": [],
        }

    tool_call = _parse_tool_call(last_msg)

    if tool_call:
        return {"done": False, "messages": []}

    if _is_hallucinating(last_msg) and steps < MAX_STEPS - 2:
        reminder = {
            "role": "user",
            "content": (
                "REMINDER: You must output a <TOOL_CALL> block to execute tools. "
                "Do not invent results. Please call a tool or provide your final answer."
            ),
        }
        return {"done": False, "messages": [reminder]}

    final = TOOL_CALL_PATTERN.sub("", last_msg).strip()
    return {
        "done": True,
        "final_answer": final,
        "messages": [],
    }
