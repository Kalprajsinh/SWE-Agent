from agent.retrieval.repository_map import build_repository_map
from agent.retrieval.symbols import get_symbol_text
from agent.retrieval.vector_store import get_repo_collection
import hashlib

def index_repository(repo_name: str, repo_dir: str) -> str:
    collection = get_repo_collection(repo_name)
    
    if collection.count() > 0:
        return f"Repository '{repo_name}' is already indexed ({collection.count()} symbols)."
        
    repo_map = build_repository_map(repo_dir)
    
    docs = []
    metadatas = []
    ids = []
    seen_ids = set()
    
    for rel_path, symbols in repo_map.items():
        for symbol in symbols:
            code_block = get_symbol_text(repo_dir, rel_path, symbol)
            base_id = hashlib.md5(f"{rel_path}:{symbol}".encode()).hexdigest()
            doc_id = base_id
            
            counter = 1
            while doc_id in seen_ids:
                doc_id = f"{base_id}_{counter}"
                counter += 1
                
            seen_ids.add(doc_id)
            
            docs.append(code_block)
            metadatas.append({
                "file": rel_path,
                "symbol": symbol
            })
            ids.append(doc_id)
            
    if not docs:
        return "No symbols found to index."
        
    collection.add(
        documents=docs,
        metadatas=metadatas,
        ids=ids
    )
    
    return f"Successfully indexed {len(docs)} symbols for repository '{repo_name}'."
