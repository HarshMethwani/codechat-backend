# CodeChat Backend

A code-aware chatbot API that allows you to ask questions about any GitHub repository using semantic search and Google Gemini LLM.

## Features

- **Multi-language Support:** Python, JavaScript, TypeScript, Go, Rust, Java
- **Semantic Code Parsing:** Uses Tree-Sitter AST parsing to extract functions and classes
- **Vector Similarity Search:** Finds relevant code using sentence-transformers embeddings
- **Conversation Memory:** Maintains chat history for contextual responses
- **Streaming API:** Real-time response streaming via Server-Sent Events

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Server                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  /clone ──────► git_service.py ──────► ./data/repos/        │
│                                                              │
│  /preprocess ──► filter_files.py ──► chunk_service.py       │
│                         │                   │                │
│                         ▼                   ▼                │
│                  File Collection      Tree-Sitter AST        │
│                         │                   │                │
│                         └───────┬───────────┘                │
│                                 ▼                            │
│                        embedding_service.py                  │
│                                 │                            │
│                                 ▼                            │
│                        ChromaDB (Vector Store)               │
│                                                              │
│  /chat ──────► embedding_service.py ──► llm_service.py      │
│                   (Search)                (Gemini API)       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
codechat/
├── main.py                    # FastAPI application
├── pyproject.toml             # Dependencies (Poetry)
├── .env                       # Environment variables
├── services/
│   ├── git_service.py         # Git repository cloning
│   ├── filter_files.py        # File collection & filtering
│   ├── chunk_service.py       # Code parsing with Tree-Sitter
│   ├── embedding_service.py   # Vector embeddings & ChromaDB
│   └── llm_service.py         # Google Gemini integration
└── data/
    ├── repos/                 # Cloned repositories
    └── vectorstore/           # ChromaDB storage
```

---

## API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{"status": "ok"}
```

---

### Clone Repository

```http
POST /clone
Content-Type: application/json

{
    "repo_url": "https://github.com/owner/repo"
}
```

**Response:**
```json
{
    "status": "success",
    "path": "./data/repos/owner/repo"
}
```

---

### Preprocess Repository

Extracts code chunks and stores embeddings in vector database.

```http
POST /preprocess
Content-Type: application/json

{
    "repo_path": "./data/repos/owner/repo"
}
```

**Response:**
```json
{
    "status": "success",
    "chunks_stored": 156
}
```

---

### Chat (Standard)

```http
POST /chat
Content-Type: application/json

{
    "repo_path": "./data/repos/owner/repo",
    "question": "How does the authentication work?",
    "history": [
        {"role": "user", "content": "What is this repo about?"},
        {"role": "model", "content": "This repository is..."}
    ]
}
```

**Response:**
```json
{
    "answer": "The authentication system uses JWT tokens...",
    "sources": [
        {"file": "/src/auth/jwt.py"},
        {"file": "/src/middleware/auth.py"}
    ]
}
```

---

### Chat (Streaming)

```http
POST /chat/stream
Content-Type: application/json

{
    "repo_path": "./data/repos/owner/repo",
    "question": "Explain the main function",
    "history": []
}
```

**Response:** `text/event-stream`

```
data: {"type": "sources", "data": [{"file": "/main.py"}]}

data: {"type": "chunk", "text": "The main"}

data: {"type": "chunk", "text": " function"}

data: {"type": "chunk", "text": " initializes..."}

data: {"type": "done"}

```

---

## Services

### git_service.py

Handles Git repository cloning.

| Function | Description |
|----------|-------------|
| `get_repo_path(url)` | Extracts owner/repo from GitHub URL |
| `clone_repo(url)` | Clones repository to `./data/repos/` |

---

### filter_files.py

Filters and collects code files from repository.

**Included Extensions:**
```
.py, .js, .ts, .tsx, .jsx, .java, .go, .rs, .md, .txt, .json, .yaml, .yml
```

**Excluded Directories:**
```
.git, .github, node_modules, venv, __pycache__, dist, build, .next, .idea, .vscode
```

**Max File Size:** 200 KB

| Function | Description |
|----------|-------------|
| `collect_files(repo_path)` | Recursively collects all supported files |
| `should_include_file(path)` | Validates file extension and size |
| `clean_file(path)` | Reads and normalizes file content |

---

### chunk_service.py

Parses code into semantic chunks using Tree-Sitter.

**Supported Languages & Extracted Nodes:**

| Language | Functions | Classes/Types |
|----------|-----------|---------------|
| Python | `function_definition` | `class_definition` |
| JavaScript | `function_declaration`, `arrow_function`, `method_definition` | `class_declaration` |
| TypeScript | `function_declaration`, `arrow_function`, `method_definition` | `class_declaration`, `interface_declaration`, `type_alias_declaration` |
| Go | `function_declaration`, `method_declaration` | `type_declaration` |
| Rust | `function_item` | `struct_item`, `enum_item`, `trait_item`, `impl_item` |
| Java | `method_declaration`, `constructor_declaration` | `class_declaration`, `interface_declaration` |

**CodeChunk Model:**
```python
class CodeChunk(BaseModel):
    file_path: str
    start_line: int | None
    end_line: int | None
    chunk_size: int
    name: str           # Function/class name
    content: str        # Source code
```

| Function | Description |
|----------|-------------|
| `extract_chunks_from_file(path, ext)` | Main entry - extracts chunks from file |
| `walk_tree(node, ext, path)` | Recursively traverses AST |
| `chunk_file(path, ext)` | Fallback chunking for unsupported languages |

---

### embedding_service.py

Manages vector embeddings and ChromaDB operations.

**Model:** `all-MiniLM-L6-v2` (384-dimensional embeddings)

| Function | Description |
|----------|-------------|
| `get_collection_name(repo_path)` | Generates collection name from repo path |
| `get_embedding_model()` | Lazy-loads sentence-transformers model |
| `embed_and_store(chunks, repo_name)` | Embeds and stores chunks in ChromaDB |
| `search(query, repo_name, top_k=5)` | Semantic search for relevant chunks |

---

### llm_service.py

Integrates with Google Gemini API.

**Model:** `gemini-2.5-flash-lite`

**System Prompt:**
> "You are a helpful code assistant. Consider the conversation history when responding. Use the provided code context to answer code questions."

| Function | Description |
|----------|-------------|
| `build_context(chunks)` | Formats chunks into context string |
| `call_llm(question, history, context)` | Standard LLM call |
| `call_llm_stream(question, history, context, sources)` | Streaming LLM call with SSE |

---

## Setup

### Prerequisites

- Python >= 3.10
- Poetry (package manager)
- Google Gemini API key

### Installation

```bash
# Clone the repository
git clone https://github.com/HarshMethwani/codechat.git
cd codechat

# Install dependencies
poetry install

# Create .env file
echo "GEMINI_API=your_api_key_here" > .env
```

### Running

```bash
# Start the server
poetry run uvicorn main:app --reload

# Server runs at http://localhost:8000
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API` | Google Gemini API key |

---

## Data Flow

1. **Clone:** User provides GitHub URL → Repository cloned to `./data/repos/`

2. **Preprocess:**
   - Collect supported files (filter by extension, size, directory)
   - Parse each file with Tree-Sitter (extract functions, classes)
   - Generate embeddings using sentence-transformers
   - Store in ChromaDB with metadata

3. **Chat:**
   - Encode user question as embedding
   - Search ChromaDB for top-5 similar code chunks
   - Build context string from retrieved chunks
   - Call Gemini LLM with context + history + question
   - Return answer with source file references

---

## Dependencies

| Package | Purpose |
|---------|---------|
| fastapi | Web framework |
| gitpython | Git operations |
| tree-sitter | Code parsing |
| tree-sitter-* | Language parsers |
| chromadb | Vector database |
| sentence-transformers | Embedding model |
| google-genai | Gemini API client |
| python-dotenv | Environment variables |

---

## License

MIT
