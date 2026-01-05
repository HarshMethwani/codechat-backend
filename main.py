from fastapi import FastAPI, HTTPException
import logging
from services.git_service import clone_repo
from pydantic import BaseModel, HttpUrl
from services.filter_files import collect_files
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
    collected = collect_files(request.repo_path)
    return {'data':collected}