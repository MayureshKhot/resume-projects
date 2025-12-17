# backend/embeddings.py

from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer
import numpy as np


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """
    Load the embedding model once and cache it.
    Uses a light, fast model suitable for local use.
    """
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed_text(text: str) -> List[float]:
    """
    Returns a Python list of floats so it can be stored easily.
    """
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> List[List[float]]:
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()
