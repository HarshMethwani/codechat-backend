from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
import tree_sitter_rust as tsrust
from typing import List
from pydantic import BaseModel

class CodeChunk(BaseModel):
    file_path:str
    start_line:str
    end_line:str
    chunk_size:int
    chunk_type:str
    name:str
    content:str
    language:str

LANGUAGE_MAP = {
    ".py":("python",tspython.language()),
    ".rs":("rust",tsrust.language()),
    ".ts":("typescript",tstypescript.language_typescript()),
    ".tsx":("typescript",tstypescript.language_tsx()),
    ".js":("javascript",tsjavascript.language()),
    ".go":("go",tsgo.language()),
    ".rs":("rust",tsrust.language())
}


def get_parser(ext) -> Parser | None:
    if LANGUAGE_MAP[ext]:
        language = Language(LANGUAGE_MAP[ext][1])
        return Parser(language)
    else:
        return None
    

def extract_chunks_from_file(file_path: str, source_code: str) -> List[CodeChunk]:
    