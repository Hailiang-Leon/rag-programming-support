from fastapi import FastAPI
from src.backend.config import settings

app = FastAPI(
    title=settings.app_name,
    description="A source-grounded RAG support system for introductory programming learners.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "RAG Programming Support System API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.app_env,
    }


@app.get("/config-check")
def config_check():
    return {
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
        "vector_db_path": settings.vector_db_path,
        "collection_name": settings.collection_name,
        "top_k": settings.top_k,
        "min_retrieval_score": settings.min_retrieval_score,
    }
