import os
from agent.retrieval.parser import parse_python_file, parse_js_ts_file

def get_symbol_text(repo_dir: str, rel_path: str, symbol_name: str) -> str:

    filepath = os.path.join(repo_dir, rel_path)
    
    if not os.path.exists(filepath):
        return f"File {rel_path} not found."
        
    if rel_path.endswith(".py"):
        symbols = parse_python_file(filepath, rel_path)
        lang = "python"
    elif rel_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        symbols = parse_js_ts_file(filepath, rel_path)
        lang = "javascript"
    else:
        return f"Unsupported file type for symbol extraction: {rel_path}"
    
    target_symbol = next((s for s in symbols if s.symbol == symbol_name), None)
    
    if not target_symbol:
        return f"Symbol '{symbol_name}' not found in {rel_path}."
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
          
        imports = []
        for line in lines:
            line_strip = line.strip()
            if line_strip.startswith("import ") or line_strip.startswith("from "):
                imports.append(line_strip)
              
        start_idx = target_symbol.start_line - 1
        end_idx = target_symbol.end_line
        
        symbol_code = "".join(lines[start_idx:end_idx])
        
        output_blocks = []
        output_blocks.append(f"```{lang}")
        output_blocks.append(f"# {rel_path} - {symbol_name}")
        if imports:
            output_blocks.append("\n".join(imports))
            output_blocks.append("") 
        output_blocks.append(symbol_code.rstrip("\n"))
        output_blocks.append("```")
        
        return "\n".join(output_blocks)
    except Exception as e:
        return f"Error extracting symbol: {e}"
