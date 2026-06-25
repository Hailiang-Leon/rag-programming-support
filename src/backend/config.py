import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = os.getenv("APP_NAME", "RAG Programming Support System")
    app_env: str = os.getenv("APP_ENV", "development")

    backend_host: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1")

    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./data/processed/chroma_db")
    collection_name: str = os.getenv("COLLECTION_NAME", "programming_sources")

    top_k: int = int(os.getenv("TOP_K", "5"))
    min_retrieval_score: float = float(os.getenv("MIN_RETRIEVAL_SCORE", "0.35"))

    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
