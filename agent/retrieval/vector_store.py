import chromadb
from chromadb.config import Settings
import os

_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        persist_dir = os.path.join(os.getcwd(), ".chroma_db")
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
    return _chroma_client

def get_repo_collection(repo_name: str):

    client = get_chroma_client()
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in repo_name)
    return client.get_or_create_collection(name=safe_name)
