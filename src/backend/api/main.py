from fastapi import FastAPI, HTTPException

from src.backend.api.schemas import RetrieveRequest, RetrieveResponse
from src.backend.config import settings
from src.backend.rag.retriever import (
    format_retrieval_results,
    retrieve_relevant_chunks,
)

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


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest):
    """
    Retrieve source chunks that are relevant to a learner's programming question.

    This endpoint exposes the retrieval layer of the RAG pipeline before
    answer generation is added.
    """
    try:
        chunks = retrieve_relevant_chunks(
            query=request.query,
            top_k=request.top_k,
            min_similarity_score=request.min_similarity_score,
        )

        results = format_retrieval_results(chunks)

        return {
            "query": request.query,
            "chunks_returned": len(results),
            "results": results,
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(error)}",
        ) from error