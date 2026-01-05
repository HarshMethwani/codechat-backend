from fastapi import FastAPI, HTTPException
import logging
from services.git_service import clone_repo
from pydantic import BaseModel, HttpUrl
app = FastAPI()

logging.basicConfig(filename='logger.log',format='%(asctime)s %(message)s',filemode='w')
logger = logging.getLogger()


class CloneRepository(BaseModel):
    repo_url:HttpUrl

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