from git import Repo
import os
from urllib.parse import urlparse

BASE_PATH = './data/repos'

def get_repo_path(repo_url:str):
    path = urlparse(repo_url).path.strip('/')
    owner, repo = path.split('/')[:2]
    repo = repo.replace(".git","")
    return os.path.join(BASE_PATH,owner,repo)


def clone_repo(repo_url:str):
    repo_path = get_repo_path(repo_url)
    if os.path.exists(repo_path):
        return f"Repository already exists with path {repo_path}"
    Repo.clone_from(repo_url,repo_path)
    return repo_path
