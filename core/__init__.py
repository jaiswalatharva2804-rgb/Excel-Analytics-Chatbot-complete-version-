"""Core module - shared LLM, embeddings, config, and database utilities."""
from .config import Config
from .llm import call_llm
from .database import Database

# Lazy import for embeddings to avoid loading heavy ML libraries on import
def embed(texts):
    """Generate embeddings for texts (lazy loads the model)."""
    from .embeddings import embed as _embed
    return _embed(texts)

__all__ = ["Config", "call_llm", "embed", "Database"]
