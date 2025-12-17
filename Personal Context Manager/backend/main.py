# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict

from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


from .vector_store import VectorStore

app = FastAPI(title="Personal Context OS")

# For MVP we allow all origins (Streamlit runs on another port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # relax for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_store = VectorStore(path="./chroma_db")


# ---------- Pydantic Models ----------

class ContextItemIn(BaseModel):
    title: str
    category: str  # e.g. "professional", "personal", "skills"
    content: str


class ContextItemOut(BaseModel):
    id: str
    title: str
    category: str
    content: str


class QueryRequest(BaseModel):
    query: str
    category: Optional[str] = None
    top_k: int = 5


class QueryResultItem(BaseModel):
    id: str
    title: str
    category: str
    content: str
    distance: float


class QueryResponse(BaseModel):
    query: str
    category: Optional[str]
    top_k: int
    results: List[QueryResultItem]
    context_bundle: str
    optimized: str  # NEW



# ---------- Helper: build context bundle ----------

def build_context_bundle(results: List[Dict]) -> str:
    """
    Turns raw search hits into a clean context string
    that you can paste directly into another AI tool.
    """
    if not results:
        return "No relevant context found."

    lines = []
    lines.append("### USER CONTEXT BUNDLE")
    lines.append("")
    for i, r in enumerate(results, start=1):
        meta = r["metadata"] or {}
        title = meta.get("title", f"Item {i}")
        category = meta.get("category", "general")
        content = r["content"].strip()

        lines.append(f"#### [{i}] {title} (category: {category})")
        lines.append(content)
        lines.append("")

    lines.append("### END OF CONTEXT")
    return "\n".join(lines)

def optimize_context_with_groq(query: str, results: List[QueryResultItem]) -> str:
    raw_text = "\n\n".join([f"{r.title}: {r.content}" for r in results])

    prompt = f"""
You are a context optimizer for AI systems.

User query:
{query}

Retrieved raw context:
{raw_text}

TASK:
- Clean and compress the text
- Remove fluff and repetition
- Extract only essential facts
- Convert it into a clean, minimal JSON
- MUST be optimized for token usage
- Field names must be simple and predictable

Return ONLY valid JSON. No explanations.
"""

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content



# ---------- Routes ----------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/contexts", response_model=ContextItemOut)
def add_context(item: ContextItemIn):
    doc_id = vector_store.add_context(
        title=item.title,
        category=item.category,
        content=item.content,
    )
    return ContextItemOut(
        id=doc_id,
        title=item.title,
        category=item.category,
        content=item.content,
    )


@app.get("/contexts", response_model=List[ContextItemOut])
def list_contexts():
    items = vector_store.get_all()
    return [
        ContextItemOut(
            id=i["id"],
            title=i["metadata"].get("title", "Untitled"),
            category=i["metadata"].get("category", "unknown"),
            content=i["content"],
        )
        for i in items
    ]


@app.post("/query", response_model=QueryResponse)
def query_context(q: QueryRequest):
    hits = vector_store.search(
        query=q.query,
        top_k=q.top_k,
        category=q.category,
    )

    bundle = build_context_bundle(hits)

    results = [
        QueryResultItem(
            id=h["id"],
            title=h["metadata"].get("title", "Untitled"),
            category=h["metadata"].get("category", "unknown"),
            content=h["content"],
            distance=float(h["distance"]),
        )
        for h in hits
    ]
    optimized_json = optimize_context_with_groq(q.query, results)

    return QueryResponse(
    query=q.query,
    category=q.category,
    top_k=q.top_k,
    results=results,
    context_bundle=bundle,
    optimized=optimized_json  # <-- new field!
)

