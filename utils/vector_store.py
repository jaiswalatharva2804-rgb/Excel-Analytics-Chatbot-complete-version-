"""FAISS-based vector store for similarity search."""
import faiss
import numpy as np


class VectorStore:
    """FAISS vector store for efficient similarity search."""
    
    def __init__(self, embeddings: np.ndarray = None):
        """
        Initialize vector store.
        
        Args:
            embeddings: Optional initial embeddings to add
        """
        self.index = None
        self.dimension = None
        
        if embeddings is not None:
            self.build(embeddings)
    
    def build(self, embeddings: np.ndarray):
        """
        Build the index from embeddings.
        
        Args:
            embeddings: numpy array of shape (n_samples, dimension)
        """
        embeddings = embeddings.astype("float32")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        self.dimension = embeddings.shape[1]
        
        # Create FAISS index (Inner Product = cosine similarity after normalization)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings)
    
    def add(self, embeddings: np.ndarray):
        """
        Add more embeddings to the index.
        
        Args:
            embeddings: numpy array of embeddings to add
        """
        if self.index is None:
            self.build(embeddings)
            return
        
        embeddings = embeddings.astype("float32")
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> np.ndarray:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding (1, dimension) or (dimension,)
            k: Number of results to return
            
        Returns:
            Array of indices of the k most similar vectors
        """
        if self.index is None:
            raise ValueError("Index not built. Call build() first.")
        
        query = query_embedding.astype("float32")
        
        # Ensure 2D shape
        if query.ndim == 1:
            query = query.reshape(1, -1)
        
        # Normalize query
        faiss.normalize_L2(query)
        
        # Search
        _, indices = self.index.search(query, k)
        return indices[0]
    
    def search_with_scores(self, query_embedding: np.ndarray, k: int = 5):
        """
        Search for similar vectors with similarity scores.
        
        Args:
            query_embedding: Query embedding
            k: Number of results
            
        Returns:
            Tuple of (indices, scores)
        """
        if self.index is None:
            raise ValueError("Index not built. Call build() first.")
        
        query = query_embedding.astype("float32")
        
        if query.ndim == 1:
            query = query.reshape(1, -1)
        
        faiss.normalize_L2(query)
        
        scores, indices = self.index.search(query, k)
        return indices[0], scores[0]
    
    @property
    def size(self) -> int:
        """Return number of vectors in the index."""
        return self.index.ntotal if self.index else 0


if __name__ == "__main__":
    # Test
    embeddings = np.random.rand(10, 4).astype("float32")
    store = VectorStore(embeddings)
    
    query = np.random.rand(1, 4).astype("float32")
    indices = store.search(query, k=3)
    print("Top 3 indices:", indices)
