import json
import re
from typing import AsyncGenerator

from agent import llm
from agent.tools.registry import TOOLS
from langsmith import traceable

def _build_system_prompt(repo: str = "") -> str:
    tool_docs = []
    for name, meta in TOOLS.items():
        params = "\n".join(f'      "{k}": "{v}"' for k, v in meta["parameters"].items())
        tool_docs.append(
            f'- **{name}**: {meta["description"]}\n'
            f'  Parameters:\n{params}'
        )

    tools_section = "\n\n".join(tool_docs)

    repo_context = ""
    if repo:
        repo_dir = repo.replace("/", "_")
        repo_context = f"\n\nACTIVE REPOSITORY: {repo}\nIMPORTANT: All relative paths MUST be prefixed with `{repo_dir}/`. For example, to read `package.json`, you must request `{repo_dir}/package.json`."

    return f"""You are a sophisticated AI coding agent. Your speciality is analysing GitHub repositories and improving their test coverage.{repo_context}

You have access to the following tools. To call a tool, output a JSON block wrapped in <TOOL_CALL> tags like this:

<TOOL_CALL>
{{"tool": "tool_name", "args": {{"param1": "value1", "param2": "value2"}}}}
</TOOL_CALL>

After I execute the tool, I will give you the result wrapped in <TOOL_RESULT> tags. You can then call another tool or provide your final answer.

## Available Tools

{tools_section}

## Workflow for Coverage Tasks
1. Clone the repo with `clone_repo`.
2. Explore its structure using `list_files`.
3. Read source files and existing tests with `read_file`.
4. Run the existing test suite with `run_command` to see current coverage.
5. Write new test files with `write_file`.
6. Verify the new tests pass with `run_command`.
7. Create a Pull Request with `create_pr`.

Always think step by step. After each tool result, reason about what to do next before calling the next tool.
When you have finished all tasks, provide a clear final summary without any TOOL_CALL blocks.

CRITICAL RULES:
1. You MUST call a real tool before stating any result. NEVER invent or hallucinate results.
2. ALWAYS wait for the <TOOL_RESULT> before continuing.
3. NEVER call a tool that is not in the list above.

EXAMPLE OF CORRECT BEHAVIOUR:
User: List the files
Assistant:
I will list the files in the repository.
<TOOL_CALL>
{{"tool": "list_files", "args": {{"directory": "owner_repo"}}}}
</TOOL_CALL>
User: <TOOL_RESULT>
📄 src/index.js
📄 server.js
</TOOL_RESULT>
Assistant: I can see two files. Now I'll read index.js.
<TOOL_CALL>
{{"tool": "read_file", "args": {{"file_path": "owner_repo/src/index.js"}}}}
</TOOL_CALL>"""

HALLUCINATION_SIGNALS = ["I will call", "I will run", "Result:", "will now run", "Output:", "Resulting"]

def _is_hallucinating(text: str) -> bool:
    no_tool_call = not TOOL_CALL_PATTERN.search(text)
    has_signals = any(s in text for s in HALLUCINATION_SIGNALS)
    return no_tool_call and has_signals

TOOL_CALL_PATTERN = re.compile(r"<TOOL_CALL>\s*(\{.*?\})\s*</TOOL_CALL>", re.DOTALL)

def _parse_tool_call(text: str) -> dict | None:
    match = TOOL_CALL_PATTERN.search(text)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None

@traceable(run_type="tool")
def _dispatch(tool_name: str, args: dict) -> str:
    if tool_name not in TOOLS:
        return f"Unknown tool: '{tool_name}'. Available tools: {', '.join(TOOLS.keys())}"
    fn = TOOLS[tool_name]["fn"]
    try:
        return fn(**args)
    except TypeError as e:
        return f"Tool call error (wrong args?): {e}"
    except Exception as e:
        return f"Tool execution error: {e}"

@traceable(run_type="chain")
def run(user_message: str, repo: str = "", max_steps: int = 50) -> str:
    messages = [
        {"role": "system", "content": _build_system_prompt(repo)},
        {"role": "user", "content": user_message},
    ]

    for step in range(max_steps):
        response = llm.chat(messages)
        messages.append({"role": "assistant", "content": response})

        tool_call = _parse_tool_call(response)
        if not tool_call:
            if _is_hallucinating(response) and step < max_steps - 2:
                messages.append({
                    "role": "user",
                    "content": "REMINDER: You must output a <TOOL_CALL> block to execute tools. Do not invent results. Please call a tool or provide your final answer."
                })
                continue
            final = TOOL_CALL_PATTERN.sub("", response).strip()
            return final

        tool_name = tool_call.get("tool", "")
        args = tool_call.get("args", {})
        result = _dispatch(tool_name, args)

        tool_result_msg = f"<TOOL_RESULT>\n{result}\n</TOOL_RESULT>"
        messages.append({"role": "user", "content": tool_result_msg})

    return "Max steps reached. The agent did not produce a final answer."

@traceable(run_type="chain")
async def stream_run(user_message: str, repo: str = "", max_steps: int = 35) -> AsyncGenerator[dict, None]:
    messages = [
        {"role": "system", "content": _build_system_prompt(repo)},
        {"role": "user", "content": user_message},
    ]

    for step in range(max_steps):
        full_response = ""
        try:
            async for token in llm.stream_chat(messages):
                full_response += token
                yield {"type": "token", "data": token}
        except Exception as e:
            yield {"type": "error", "data": f"LLM stream error: {e}"}
            return

        print(f"sended input {messages[-2]['content']}")
        print(f"\n\033[96m--- [RAW AGENT RESPONSE | STEP {step}] ---\033[0m\n{full_response}\n\033[96m----------------------------------------\033[0m\n")

        messages.append({"role": "assistant", "content": full_response})

        tool_call = _parse_tool_call(full_response)
        if not tool_call:
            if _is_hallucinating(full_response) and step < max_steps - 2:
                yield {"type": "token", "data": "\n\n*(System: Detected missing tool call. Re-prompting model...)*\n"}
                messages.append({
                    "role": "user",
                    "content": "REMINDER: You must output a <TOOL_CALL> block to execute tools. Do not invent results. Please call a tool or provide your final answer."
                })
                continue
            
            yield {"type": "done", "data": ""}
            return

        tool_name = tool_call.get("tool", "")
        args = tool_call.get("args", {})
        yield {"type": "tool_call", "data": {"tool": tool_name, "args": args}}

        result = _dispatch(tool_name, args)
        yield {"type": "tool_result", "data": result}
        
        print(f"\n\033[93m--- [TOOL RESULT] ---\033[0m\n{result[:1000]}{'...' if len(result) > 1000 else ''}\n\033[93m---------------------\033[0m\n")

        tool_result_msg = f"<TOOL_RESULT>\n{result}\n</TOOL_RESULT>"
        messages.append({"role": "user", "content": tool_result_msg})

    yield {"type": "error", "data": "Max steps reached without a final answer."}
