import os
import json
from pathlib import Path
from agent.retrieval.parser import parse_python_file, parse_js_ts_file

def build_repository_map(repo_dir: str) -> dict:
    repo_map = {}
    base_path = Path(repo_dir)
    
    for root, _, files in os.walk(base_path):
        
        if any(part.startswith('.') or part == 'node_modules' for part in Path(root).parts):
            continue
            
        for file in files:
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, repo_dir).replace("\\", "/")
            
            if file.endswith(".py"):
                symbols = parse_python_file(filepath, rel_path)
            elif file.endswith((".js", ".jsx", ".ts", ".tsx")):
                symbols = parse_js_ts_file(filepath, rel_path)
            elif file.endswith((".json", ".md", "requirements.txt", ".toml", ".yml", ".yaml")) or file.endswith(".config.js"):
                symbols = []
            else:
                continue
                
            if symbols:
                repo_map[rel_path] = [s.symbol for s in symbols]
            else:
                repo_map[rel_path] = []  
                    
    return repo_map


def get_repository_map_formatted(repo_dir: str) -> str:

    repo_map = build_repository_map(repo_dir)
    lines = []
    
    for file, symbols in repo_map.items():
        lines.append(f"[FILE] {file}")
        for sym in symbols:
            if "." in sym:
                
                lines.append(f"   |-- {sym.split('.')[-1]}()")
            else:
                lines.append(f" |-- {sym}")
    
    if not lines:
        return "No parsed files or symbols found in this repository."
        
    return "\n".join(lines)
