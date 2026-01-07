import chromadb
from sentence_transformers import SentenceTransformer
from chunk_service import CodeChunk
from typing import List




CHROMA_PATH = "./data/vectorstore"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_model = None
def get_embedding_model() -> SentenceTransformer:
      global _model
      if _model is None:     
        _model = SentenceTransformer(EMBEDDING_MODEL)
      return _model


def get_or_create_collection(repo_name: str):
      chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
      collection = chroma_client.get_or_create_collection(name=repo_name)
      return collection



def embed_and_store(chunks: List[CodeChunk], repo_name: str) -> int:
        model = get_embedding_model()
        collection = get_or_create_collection(repo_name)
        id = [f"{chunk.file_path}_{i}" for i, chunk in enumerate(chunks)]
        documents = [e.content for e in chunks]
        metadata = [{"file_path":e.file_path,"name":e.name,"chunk_size":e.chunk_size} for e in chunks]
        embeddings = []
        contents = [chunk.content for chunk in chunks]
        embeddings = model.encode(contents)
        collection.add(
                ids=id,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadata
            )
        return len(chunks)


def search(query: str, repo_name: str, top_k: int = 5) -> List[dict]:
      model = get_embedding_model()
      collection = get_or_create_collection(repo_name)

      embedded_query = model.encode(query).tolist()
      results = collection.query(
            query_texts=[embedded_query],
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

