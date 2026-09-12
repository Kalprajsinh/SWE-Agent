from agent.retrieval.vector_store import get_repo_collection

def search_repository(repo_name: str, query: str, top_k: int = 5) -> str:

    collection = get_repo_collection(repo_name)
    
    if collection.count() == 0:
        return f"Repository '{repo_name}' is not indexed. Please index it first."
        
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    
    if not results or not results['documents'] or not results['documents'][0]:
        return "No relevant code found."
        
    output = []
    output.append(f"Found {len(results['documents'][0])} relevant code snippets for '{query}':\n")
    
    for i, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][i]
        output.append(f"--- MATCH {i+1} | {meta['file']} | {meta['symbol']} ---")
        output.append(doc)
        output.append("")
        
    return "\n".join(output)
