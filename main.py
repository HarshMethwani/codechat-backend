from fastapi import FastAPI, HTTPException
import logging
from services.git_service import clone_repo
from pydantic import BaseModel, HttpUrl
from services.filter_files import collect_files
from services.embedding_service import search, embed_and_store,get_collection_name
from services.chunk_service import extract_chunks_from_file
from services.llm_service import build_context,call_llm,call_llm_stream
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List
app = FastAPI()

logging.basicConfig(filename='logger.log',format='%(asctime)s %(message)s',filemode='w')
logger = logging.getLogger()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CloneRepository(BaseModel):
    repo_url:HttpUrl

class RepoPath(BaseModel):
    repo_path:str

class ChatRequest(BaseModel):
    repo_path:str
    question:str
    history:List[dict] = []

class ChatResponse(BaseModel):
    answer:str
    sources:List[dict]

@app.get('/health')
def health():
    return {"status":"ok"} 


@app.post('/clone')
def clone_repository(request:CloneRepository):
    try:
        target_path = clone_repo(str(request.repo_url))
        return {
            "status":"success",
            "path":target_path
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/preprocess")
def preprocess(request:RepoPath):
    files = collect_files(request.repo_path)
    all_chunks = []
    for file in files:
        ext = Path(file["path"]).suffix
        chunks = extract_chunks_from_file(file["path"],ext)
        all_chunks.extend(chunks)
    
    repo_name = get_collection_name(request.repo_path)
    count = embed_and_store(all_chunks,repo_name)
    return {"status":"success","chunks_stored":count}


@app.post('/chat')
def chat(request:ChatRequest):
    repo_name = get_collection_name(request.repo_path)
    relevant_chunks = search(request.question,repo_name)
    context = build_context(relevant_chunks)
    sources = [{"file": str(c["metadata"]["file_path"]).replace("./data/repos","")} for c in relevant_chunks]
    answer = call_llm(request.question,request.history,context)
    return ChatResponse(answer=answer, sources=sources)

@app.post('/chat/stream')
def chat_stream(request:ChatRequest):
    repo_name = get_collection_name(request.repo_path)
    relevant_chunks = search(request.question,repo_name)
    context = build_context(relevant_chunks)
    sources = [{"file": str(c["metadata"]["file_path"]).replace("./data/repos","")} for c in relevant_chunks]
    # answer = call_llm(request.question,request.history,context)
    return StreamingResponse(call_llm_stream(request.question,request.history,context,sources),media_type='text/event-stream')

