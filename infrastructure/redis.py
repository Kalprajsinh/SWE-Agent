import os
import json
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def get_chat_history(session_id: str) -> list:

    if not session_id:
        return []
    
    key = f"chat:{session_id}:messages"
    messages_json = redis_client.lrange(key, 0, -1)
    
    messages = []
    for msg in messages_json:
        try:
            messages.append(json.loads(msg))
        except json.JSONDecodeError:
            continue
            
    return messages

def save_chat_history(session_id: str, messages: list):
    if not session_id or not messages:
        return
        
    key = f"chat:{session_id}:messages"
    
    redis_client.delete(key)
    for msg in messages:
        redis_client.rpush(key, json.dumps(msg))
        
    redis_client.expire(key, 86400)

def set_run_status(run_id: str, status: str):

    key = f"run:{run_id}:status"
    redis_client.set(key, status, ex=86400)

def get_run_status(run_id: str) -> str:
    key = f"run:{run_id}:status"
    return redis_client.get(key) or "UNKNOWN"

def add_run_event(run_id: str, event_name: str, details: dict = None):

    key = f"run:{run_id}:events"
    event = {
        "event": event_name,
        "details": details or {}
    }
    redis_client.rpush(key, json.dumps(event))
    redis_client.expire(key, 86400)

def get_run_events(run_id: str) -> list:
    key = f"run:{run_id}:events"
    events_json = redis_client.lrange(key, 0, -1)
    events = []
    for evt in events_json:
        try:
            events.append(json.loads(evt))
        except json.JSONDecodeError:
            continue
    return events
