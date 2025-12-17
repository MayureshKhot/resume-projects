import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
from utils import extract_text, chunk_text

load_dotenv()

class RAGPipeline:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.chunks = []
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        os.makedirs('embeddings', exist_ok=True)
        os.makedirs('data/uploaded_pdfs', exist_ok=True)
        
        self._load_index()
    
    def _load_index(self):
        """Load existing FAISS index if available"""
        if os.path.exists('embeddings/faiss_index.bin') and os.path.exists('embeddings/chunks.json'):
            self.index = faiss.read_index('embeddings/faiss_index.bin')
            with open('embeddings/chunks.json', 'r') as f:
                self.chunks = json.load(f)
            print(f"Loaded {len(self.chunks)} chunks from index")
    
    def _save_index(self):
        """Save FAISS index and chunks"""
        faiss.write_index(self.index, 'embeddings/faiss_index.bin')
        with open('embeddings/chunks.json', 'w') as f:
            json.dump(self.chunks, f)
        print(f"Saved {len(self.chunks)} chunks to index")
    
    def add_document(self, file_path):
        """Process and add document to vector DB"""
        print(f"Extracting text from {file_path}...")
        text = extract_text(file_path)
        
        print("Chunking text...")
        new_chunks = chunk_text(text)
        
        print("Generating embeddings...")
        embeddings = self.model.encode(new_chunks)
        
        if self.index is None:
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
        
        self.index.add(np.array(embeddings).astype('float32'))
        self.chunks.extend(new_chunks)
        
        self._save_index()
        print(f"Added {len(new_chunks)} chunks to database")
    
    def query(self, question, top_k=3):
        """Query the RAG system"""
        if self.index is None or len(self.chunks) == 0:
            return "No documents in database. Please add documents first."
        
        print(f"Searching for relevant context...")
        query_embedding = self.model.encode([question])
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), top_k)
        
        context = '\n\n'.join([self.chunks[i] for i in indices[0]])
        
        print(" Generating answer with Groq LLM...")
        prompt = f"""Use the context below to answer the question. If you cannot answer from the context, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        response = self.groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024
        )
        
        return response.choices[0].message.content
