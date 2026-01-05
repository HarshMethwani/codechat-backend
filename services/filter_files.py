import os
from typing import List
INCLUDE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx",
    ".java", ".go", ".rs",
    ".md", ".txt", ".json", ".yaml", ".yml"
}

EXCLUDE_DIRS = {
    ".git", ".github", "node_modules", "venv",
    "__pycache__", "dist", "build", ".next",
    ".idea", ".vscode"
}

MAX_FILE_SIZE = 200_000  


def should_include_file(file_path:str)->bool:
    _,ext = os.path.splitext(file_path)
    if ext.lower() not in INCLUDE_EXTENSIONS:
        return False
    
    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        return False
    
    return True
    

def collect_files(repo_path:str)->List[str]:
    collected = []
    for root,dirs, file in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for _file in file:
            full_path  = os.path.join(root,_file)
            if should_include_file(full_path):
                collected.append(full_path)
    
    return collected

def clean_file(file_path:str)->str:
    try:
        with open(file_path,mode='r', encoding='utf-8') as f:
            content = f.read()
            return normalize_text(content)
    except Exception:
        return ""
        


def normalize_text(text:str)->str:
        normalized = text.replace('x00',"")
        normalized = text.strip()
        return normalized