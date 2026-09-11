import ast
import os
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class SymbolInfo:
    file: str
    symbol: str
    start_line: int
    end_line: int
    type: str 

    def to_dict(self):
        return asdict(self)


def parse_python_file(filepath: str, rel_path: str) -> List[SymbolInfo]:
    symbols = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
            tree = ast.parse(source, filename=filepath)
    except Exception as e:
        print(f"[WARN] Failed to parse {rel_path}: {e}")
        return symbols

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            symbols.append(SymbolInfo(
                file=rel_path,
                symbol=node.name,
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                type="class"
            ))
            
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(SymbolInfo(
                        file=rel_path,
                        symbol=f"{node.name}.{child.name}",
                        start_line=child.lineno,
                        end_line=child.end_lineno or child.lineno,
                        type="method"
                    ))

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(SymbolInfo(
                file=rel_path,
                symbol=node.name,
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                type="function"
            ))

    return symbols


import re

def parse_js_ts_file(filepath: str, rel_path: str) -> List[SymbolInfo]:

    symbols = []
    
    class_pattern = re.compile(r'(?:export\s+)?(?:default\s+)?class\s+([a-zA-Z0-9_]+)')
    func_pattern = re.compile(r'(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(')
    arrow_pattern = re.compile(r'(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>')
    route_pattern = re.compile(r'([a-zA-Z0-9_]+)\.(get|post|put|delete|patch|all|use)\s*\(')

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[WARN] Failed to read {rel_path}: {e}")
        return symbols

    in_symbol = None
    bracket_count = 0
    start_line = 0

    for i, line in enumerate(lines):
        line_num = i + 1
        
        if in_symbol:
            bracket_count += line.count('{')
            bracket_count -= line.count('}')
            
            if bracket_count <= 0:
              
                symbols.append(SymbolInfo(
                    file=rel_path,
                    symbol=in_symbol["name"],
                    start_line=in_symbol["start"],
                    end_line=line_num,
                    type=in_symbol["type"]
                ))
                in_symbol = None
                bracket_count = 0
            continue
            
        class_match = class_pattern.search(line)
        func_match = func_pattern.search(line) or arrow_pattern.search(line)
        route_match = route_pattern.search(line)
        
        if class_match:
            in_symbol = {"name": class_match.group(1), "start": line_num, "type": "class"}
            bracket_count = line.count('{') - line.count('}')

            if bracket_count <= 0 and '{' in line:
                symbols.append(SymbolInfo(
                    file=rel_path,
                    symbol=in_symbol["name"],
                    start_line=line_num,
                    end_line=line_num,
                    type="class"
                ))
                in_symbol = None
                bracket_count = 0
        elif func_match:
            in_symbol = {"name": func_match.group(1), "start": line_num, "type": "function"}
            bracket_count = line.count('{') - line.count('}')
            if bracket_count <= 0 and '{' in line:
                symbols.append(SymbolInfo(
                    file=rel_path,
                    symbol=in_symbol["name"],
                    start_line=line_num,
                    end_line=line_num,
                    type="function"
                ))
                in_symbol = None
                bracket_count = 0
        elif route_match:
            in_symbol = {"name": f"{route_match.group(1)}.{route_match.group(2)}", "start": line_num, "type": "route"}
            bracket_count = line.count('{') - line.count('}')
            if bracket_count <= 0 and '{' in line:
                symbols.append(SymbolInfo(
                    file=rel_path,
                    symbol=in_symbol["name"],
                    start_line=line_num,
                    end_line=line_num,
                    type="route"
                ))
                in_symbol = None
                bracket_count = 0

    if in_symbol:
        symbols.append(SymbolInfo(
            file=rel_path,
            symbol=in_symbol["name"],
            start_line=in_symbol["start"],
            end_line=len(lines),
            type=in_symbol["type"]
        ))

    return symbols
