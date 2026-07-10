from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi import FastAPI

from src.backend.api.schemas import (
    AskRequest,
    AskResponse,
    RetrieveRequest,
    RetrieveResponse,
    RetrievedChunkResponse,
)
from src.backend.config import settings
from src.backend.rag.generator import (
    generate_source_grounded_answer,
    generated_answer_to_dict,
)
from src.backend.rag.retriever import retrieve_relevant_chunks
from src.backend.storage.query_log_repository import save_query_log


app = FastAPI(
    title=settings.app_name,
    description="Source-grounded RAG support system for introductory programming learners.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.app_env,
    }


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve_sources(request: RetrieveRequest) -> RetrieveResponse:
    chunks = retrieve_relevant_chunks(
        query=request.query,
        top_k=request.top_k,
        min_similarity_score=request.min_similarity_score,
    )

    results = [
        RetrievedChunkResponse(
            rank=index + 1,
            chunk_id=chunk.chunk_id,
            source=chunk.source,
            text_preview=chunk.text[:300],
            distance=round(chunk.distance, 4),
            similarity_score=round(chunk.similarity_score, 4),
        )
        for index, chunk in enumerate(chunks)
    ]

    return RetrieveResponse(
        query=request.query,
        chunks_returned=len(results),
        results=results,
    )


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest) -> AskResponse:
    generated_answer = generate_source_grounded_answer(
        query=request.query,
        top_k=request.top_k,
        min_similarity_score=request.min_similarity_score,
    )

    result = generated_answer_to_dict(generated_answer)

    save_query_log(
        query=result["query"],
        answer_status=result["answer_status"],
        answer=result["answer"],
        sources=result["sources"],
    )

    return AskResponse(**result)

# Frontend static file serving
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")
