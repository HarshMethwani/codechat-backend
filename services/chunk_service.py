from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
import tree_sitter_rust as tsrust
from typing import List
from pydantic import BaseModel
from typing import Optional
from filter_files import clean_file
from pathlib import Path
class CodeChunk(BaseModel):
    file_path:str
    start_line:Optional[int] = None
    end_line:Optional[int] = None
    chunk_size:int
    name:str
    content:str

LANGUAGE_MAP = {
    ".py":("python",tspython.language()),
    ".rs":("rust",tsrust.language()),
    ".ts":("typescript",tstypescript.language_typescript()),
    ".tsx":("typescript",tstypescript.language_tsx()),
    ".js":("javascript",tsjavascript.language()),
    ".go":("go",tsgo.language())
}

NODE_TYPE_MAP = {
    "python": {
        "function": {"function_definition"},
        "class": {"class_definition"},
    },
    "go": {
        "function": {"function_declaration", "method_declaration"},
        "class": {"type_declaration"}, 
    },
    "java": {
        "function": {"method_declaration", "constructor_declaration"},
        "class": {
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "record_declaration",
        },
    },
    "javascript": {
        "function": {
            "function_declaration",
            "function_expression",
            "arrow_function",
            "method_definition", 
        },
        "class": {"class_declaration", "class_expression"},
    },
    "typescript": {
        "function": {
            "function_declaration",
            "function_expression",
            "arrow_function",
            "method_definition",
            "method_signature", 
        },
        "class": {
            "class_declaration",
            "class_expression",
            "interface_declaration",
            "type_alias_declaration",
        },
    },
    "rust": {
        "function": {"function_item"}, 
        "class": {
            "struct_item",
            "enum_item",
            "trait_item",
            "impl_item",
        },
    },
}

def get_parser(ext) -> Parser | None:
    if ext not in LANGUAGE_MAP:
        return None
    code_lang = Language(LANGUAGE_MAP[ext][1])
    parser = Parser(code_lang)
    return parser
    

def extract_chunks_from_file(file_path: str,ext:str) -> List[CodeChunk]:
    content = clean_file(file_path)
    if(len(content)>0):
        if ext in LANGUAGE_MAP:
            print("using parse")
            parser = get_parser(ext)
            tree = parser.parse(content.encode("utf-8"))
            root_node = tree.root_node
            chunks = walk_tree(root_node,ext,file_path)
            return chunks
        else:
            print("using default")
            return chunk_file(file_path,ext)

def walk_tree(node,ext,file_path)->list:
    chunks = []
    language = LANGUAGE_MAP[ext][0]
    function_types = NODE_TYPE_MAP[language]["function"]
    class_types = NODE_TYPE_MAP[language]["class"]
    interesting_types = function_types | class_types | {"comment"}
    if node.type in interesting_types:
        name_node = node.child_by_field_name("name")
        if name_node:
            node_name = name_node.text.decode('utf8')
        elif node.type == "comment":
            node_name = "Comment"
        else:
            node_name = f"Anonymous {node.type}"
        chunks.append({
            "file_path":file_path,
            "start_line":node.start_point[0]+1,
            "end_line":node.end_point[0]+1,
            "chunk_size":len(node.text.decode('utf8')),
            "name":node_name,
            "content":node.text.decode('utf8')
        })
    for child in node.children:
        chunks.extend(walk_tree(child,ext,file_path))
    
    return chunks

def chunk_file(file_path:str,ext:str,overlap:int=150, chunk_size:int = 800)->List[CodeChunk]:
    file_content = ""
    chunk = []
    with open(file_path,'r') as f:
        file_content = f.read()
        content_length = len(file_content)
    
    start = 0
    while start < content_length:
        end = start + chunk_size
        chunk.append({
        "file_path":file_path,
        "chunk_size":end-start,
        "name":Path(file_path).name,
        "content":file_content[start:end]
        })
        start = end - overlap
    return chunk         
