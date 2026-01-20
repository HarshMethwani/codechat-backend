import chromadb
from sentence_transformers import SentenceTransformer
from services.chunk_service import CodeChunk
from typing import List
from pathlib import Path



CHROMA_PATH = "./data/vectorstore"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_model = None

def get_collection_name(repo_path:str)->str:
    parts = Path(repo_path).parts
    owner = parts[-2]
    repo = parts[-1]
    return f"{owner}_{repo}".lower()

def get_embedding_model() -> SentenceTransformer:
      global _model
      if _model is None:     
        _model = SentenceTransformer(EMBEDDING_MODEL)
      return _model


def get_or_create_collection(repo_name: str):
      chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
      collection = chroma_client.get_or_create_collection(name=repo_name)
      return collection



def embed_and_store(chunks: List[CodeChunk], repo_name: str, batch_size: int = 32) -> int:
        model = get_embedding_model()
        collection = get_or_create_collection(repo_name)

        total_stored = 0
        # Process in batches to avoid OOM
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            ids = [f"{chunk['file_path']}_{i + j}" for j, chunk in enumerate(batch)]
            documents = [e['content'] for e in batch]
            metadata = [{"file_path":e['file_path'],"name":e['name'],"chunk_size":e['chunk_size']} for e in batch]
            contents = [chunk['content'] for chunk in batch]

            embeddings = model.encode(contents)
            collection.add(
                    ids=ids,
                    embeddings=embeddings.tolist(),
                    documents=documents,
                    metadatas=metadata
                )
            total_stored += len(batch)

        return total_stored


def search(query: str, repo_name: str, top_k: int = 5) -> List[dict]:
      model = get_embedding_model()
      collection = get_or_create_collection(repo_name)

      embedded_query = model.encode(query).tolist()
      results = collection.query(
            query_embeddings=[embedded_query],
            n_results=top_k
      )
      output = []
      for i in range(len(results['ids'][0])):
            output.append({
                  "id":results['ids'][0][i],
                  "content":results['documents'][0][i],
                  "metadata":results['metadatas'][0][i],
                  "distance":results['distances'][0][i] if 'distances' in results else None
            })
      return output

