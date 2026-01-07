from fastapi import FastAPI, HTTPException
import logging
from services.git_service import clone_repo
from pydantic import BaseModel, HttpUrl
from services.filter_files import collect_files
from services.embedding_service import search, embed_and_store,get_collection_name
from services.chunk_service import extract_chunks_from_file
from pathlib import Path
app = FastAPI()

logging.basicConfig(filename='logger.log',format='%(asctime)s %(message)s',filemode='w')
logger = logging.getLogger()


class CloneRepository(BaseModel):
    repo_url:HttpUrl

class RepoPath(BaseModel):
    repo_path:str

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