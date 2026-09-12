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
2. For large repositories, index it with `index_codebase` first, then query conceptual logic using `search_codebase`.
3. For small repositories or exploring exact structure, map it with `get_repository_map`.
4. Extract specific functions and classes you need to test using `get_symbol`.
5. Run the existing test suite with `run_command` to see current coverage.
6. Write new test files with `write_file`.
7. Verify the new tests pass with `run_command`.
8. Create a Pull Request with `create_pr`.

Always think step by step. After each tool result, reason about what to do next before calling the next tool.
When you have finished all tasks, provide a clear final summary without any TOOL_CALL blocks.

CRITICAL RULES:
1. You MUST call a real tool before stating any result. NEVER invent or hallucinate results.
2. ALWAYS wait for the <TOOL_RESULT> before continuing.
3. NEVER call a tool that is not in the list above.

EXAMPLE OF CORRECT BEHAVIOUR:
User: Understand the repo
Assistant:
I will map the repository to see its structure.
<TOOL_CALL>
{{"tool": "get_repository_map", "args": {{"repo": "owner_repo"}}}}
</TOOL_CALL>
User: <TOOL_RESULT>
[FILE] src/auth.py
 |-- AuthService
   |-- login()
   |-- validate()
</TOOL_RESULT>
Assistant: I can see the AuthService class. Now I'll read the login method.
<TOOL_CALL>
{{"tool": "get_symbol", "args": {{"repo": "owner_repo", "file_path": "src/auth.py", "symbol": "AuthService.login"}}}}
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

@traceable(run_type="chain")
async def graph_stream_run(user_message: str, repo: str = "") -> AsyncGenerator[dict, None]:
    from agent.graph.graph import agent_graph

    initial_state = {
        "messages": [
            {"role": "system", "content": _build_system_prompt(repo)},
            {"role": "user", "content": user_message},
        ],
        "task": user_message,
        "repo": repo,
        "steps": 0,
        "final_answer": "",
        "done": False,
        "last_tool": "",
    }

    async for event in agent_graph.astream(initial_state, stream_mode="updates"):
        for node_name, update in event.items():
            msgs = update.get("messages", [])
            for msg in msgs:
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role == "assistant":
                 
                    chunk_size = 6
                    for i in range(0, len(content), chunk_size):
                        yield {"type": "token", "data": content[i:i + chunk_size]}

                    tool_call = _parse_tool_call(content)
                    if tool_call:
                        yield {
                            "type": "tool_call",
                            "data": {
                                "tool": tool_call.get("tool", ""),
                                "args": tool_call.get("args", {}),
                            },
                        }
                elif role == "user" and "<TOOL_RESULT>" in content:
                   
                    result_text = content.replace("<TOOL_RESULT>", "").replace("</TOOL_RESULT>", "").strip()
                    yield {"type": "tool_result", "data": result_text}
                    
            if update.get("done"):
                yield {"type": "done", "data": ""}
                return

    yield {"type": "done", "data": ""}

