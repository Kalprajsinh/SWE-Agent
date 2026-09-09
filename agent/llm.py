import os
import asyncio
import threading
import queue
from typing import AsyncGenerator
from openai import OpenAI

QWEN_API_KEY    = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL   = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1")
QWEN_MODEL      = os.getenv("QWEN_MODEL", "qwen3.8-flash")
ENABLE_THINKING = os.getenv("ENABLE_THINKING", "true").lower() == "true"


def _client() -> OpenAI:
    return OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)


def _messages_to_input(messages: list[dict]) -> str:
    parts = []
    system_part = ""
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "system":
            system_part = content
        elif role == "user":
            parts.append(f"User: {content}")
        elif role == "assistant":
            parts.append(f"Assistant: {content}")

    conversation = "\n\n".join(parts)
    if system_part:
        return f"{system_part}\n\n{conversation}\n\nAssistant:"
    return f"{conversation}\n\nAssistant:"


def _extract_answer(response) -> str:
    for item in response.output:
        if item.type == "message":
            for part in item.content:
                if hasattr(part, "text"):
                    return part.text
    return ""


def chat(messages: list[dict], model: str | None = None) -> str:
    model = model or QWEN_MODEL
    input_text = _messages_to_input(messages)

    response = _client().responses.create(
        model=model,
        input=input_text,
        extra_body={"enable_thinking": ENABLE_THINKING},
    )
    return _extract_answer(response)


async def stream_chat(messages: list[dict], model: str | None = None) -> AsyncGenerator[str, None]:
    model = model or QWEN_MODEL
    input_text = _messages_to_input(messages)
    SENTINEL = object()
    result_queue: queue.Queue = queue.Queue()

    def _worker():
        try:
            response = _client().responses.create(
                model=model,
                input=input_text,
                extra_body={"enable_thinking": ENABLE_THINKING},
            )
            answer = _extract_answer(response)
            # Emit in small chunks so the UI receives a streaming effect
            chunk_size = 6
            for i in range(0, len(answer), chunk_size):
                result_queue.put(answer[i:i + chunk_size])
        except Exception as exc:
            result_queue.put(exc)
        finally:
            result_queue.put(SENTINEL)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

    loop = asyncio.get_event_loop()
    while True:
        item = await loop.run_in_executor(None, result_queue.get)
        if item is SENTINEL:
            break
        if isinstance(item, Exception):
            raise item
        yield item


def is_available() -> bool:
    return bool(QWEN_API_KEY and QWEN_API_KEY.startswith("sk-"))
