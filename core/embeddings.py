"""Centralized embeddings using sentence-transformers."""
import os
import warnings

# Suppress warnings
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

warnings.filterwarnings("ignore")

try:
    from transformers import logging as tf_logging
    tf_logging.set_verbosity_error()
except Exception:
    pass

from sentence_transformers import SentenceTransformer
from .config import Config

# Lazy load model
_model = None


def _get_model():
    """Lazy load the embedding model. Downloads if not cached."""
    global _model
    if _model is None:
        try:
            # Try loading locally first
            _model = SentenceTransformer(
                Config.EMBEDDING_MODEL,
                local_files_only=True
            )
        except Exception:
            # Download if not available locally
            print(f"Downloading embedding model: {Config.EMBEDDING_MODEL}...")
            _model = SentenceTransformer(Config.EMBEDDING_MODEL)
            print("Model downloaded and cached.")
    return _model


def embed(texts: list[str]):
    """
    Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        numpy array of embeddings (float32)
    """
    model = _get_model()
    return model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False
    ).astype("float32")


if __name__ == "__main__":
    print(embed(["bad service", "great support"]).shape)
