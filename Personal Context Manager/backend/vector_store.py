import uuid
from typing import List, Dict, Optional

import chromadb
from chromadb.config import Settings

from .embeddings import embed_texts


class LocalEmbeddingFunction:
    def __call__(self, input):
        # Chroma expects this signature exactly.
        return self.embed_documents(input)

    def embed_documents(self, input):
        from .embeddings import embed_texts
        
        if isinstance(input, str):
            return embed_texts([input])
        if isinstance(input, list):
            return embed_texts(input)

        raise TypeError("embed_documents expects a string or list of strings.")

    def embed_query(self, input):
        from .embeddings import embed_texts
        
        if isinstance(input, str):
            return embed_texts([input])
        if isinstance(input, list):
            return embed_texts(input)

        raise TypeError("embed_query expects a string or list of strings.")

    def name(self):
        return "local-embedding"




class VectorStore:
    def __init__(self, path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(
            path=path,
            settings=Settings(allow_reset=True)
        )

        self.embedding_fn = LocalEmbeddingFunction()

        self.collection = self.client.get_or_create_collection(
            name="contexts",
            embedding_function=self.embedding_fn
        )

    def add_context(self, title: str, category: str, content: str) -> str:
        doc_id = str(uuid.uuid4())
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[{"title": title, "category": category}],
        )
        return doc_id

    def search(self, query: str, top_k: int = 5, category: Optional[str] = None) -> List[Dict]:
        where_filter = {"category": category} if category else None

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
        )

        hits = []
        for i in range(len(results["ids"][0])):
            hits.append(
                {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )
        return hits

    def get_all(self):
        results = self.collection.get()
        items = []
        for i in range(len(results["ids"])):
            items.append(
                {
                    "id": results["ids"][i],
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i],
                }
            )
        return items
