"""Configuration settings for the Excel Analytics Chatbot.

All settings can be overridden via environment variables.
The chatbot uses local models only - no API calls to external services.
"""
import os


class Config:
    """
    Central configuration for the Excel Analytics Chatbot.
    
    Environment Variables:
        OLLAMA_URL: Ollama API endpoint (default: http://localhost:11434/api/chat)
        LLM_MODEL: Model to use (default: llama3:8b)
        DB_PATH: DuckDB database path (default: data/analytics.duckdb)
        EMBEDDING_MODEL: Sentence transformer model (default: all-MiniLM-L6-v2)
    """
    
    # ===========================================
    # LLM Settings (Local Ollama)
    # ===========================================
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    DEFAULT_MODEL = os.getenv("LLM_MODEL", "llama3:8b")
    DEFAULT_TEMPERATURE = 0.1
    LLM_TIMEOUT = 120  # seconds
    
    # Alternative local models (uncomment to use)
    # DEFAULT_MODEL = "mistral:7b"
    # DEFAULT_MODEL = "codellama:7b"
    # DEFAULT_MODEL = "llama2:7b"
    
    # ===========================================
    # Embedding Settings (Local sentence-transformers)
    # ===========================================
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_LOCAL_ONLY = True  # Always use local embeddings
    
    # Alternative embedding models (local)
    # EMBEDDING_MODEL = "all-mpnet-base-v2"  # Higher quality, slower
    # EMBEDDING_MODEL = "paraphrase-MiniLM-L6-v2"  # Good for paraphrasing
    
    # ===========================================
    # Database Settings
    # ===========================================
    DB_PATH = os.getenv("DB_PATH", "data/analytics.duckdb")
    DEFAULT_TABLE = "data"
    
    # ===========================================
    # Handler Settings
    # ===========================================
    
    # Clustering
    DEFAULT_CLUSTERS = 6
    CLUSTER_SAMPLE_SIZE = 8
    MAX_CLUSTER_SAMPLES = 15
    
    # RAG (Retrieval Augmented Generation)
    RAG_TOP_K = 6
    RAG_SUB_QUESTIONS = 5
    RAG_MAX_CONTEXT = 12
    
    # SQL Handler
    SQL_MAX_RESULTS = 1000
    SQL_TIMEOUT = 30  # seconds
    
    # Hybrid Handler
    HYBRID_MAX_COLUMNS = 10
    HYBRID_TREND_POINTS = 30
    
    # Schema Handler
    SCHEMA_MAX_SAMPLES = 10
    SCHEMA_MAX_CATEGORIES = 20
    
    # ===========================================
    # General Settings
    # ===========================================
    SAMPLE_SIZE = 50
    MAX_TEXT_LENGTH = 500  # For text truncation
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        import requests
        
        # Check Ollama connection
        try:
            response = requests.get(
                cls.OLLAMA_URL.replace("/api/chat", "/api/tags"),
                timeout=5
            )
            if response.status_code != 200:
                print(f"Warning: Ollama not responding at {cls.OLLAMA_URL}")
                return False
        except Exception:
            print(f"Warning: Cannot connect to Ollama at {cls.OLLAMA_URL}")
            return False
        
        return True
    
    @classmethod
    def show(cls):
        """Print current configuration."""
        print("Excel Analytics Chatbot Configuration")
        print("=" * 40)
        print(f"LLM Model: {cls.DEFAULT_MODEL}")
        print(f"Ollama URL: {cls.OLLAMA_URL}")
        print(f"Embedding Model: {cls.EMBEDDING_MODEL}")
        print(f"Database Path: {cls.DB_PATH}")
        print(f"Debug Mode: {cls.DEBUG}")
