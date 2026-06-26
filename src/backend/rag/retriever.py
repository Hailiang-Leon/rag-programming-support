import argparse
from dataclasses import dataclass
from pathlib import Path

from src.backend.config import settings
from src.backend.rag.vector_store import (
    DEFAULT_EMBEDDING_MODEL,
    query_vector_store,
)


@dataclass
class RetrievedChunk:
    chunk_id: str
    source: str
    text: str
    distance: float
    similarity_score: float


def distance_to_similarity(distance: float) -> float:
    """
    Convert ChromaDB cosine distance into an approximate similarity score.

    With cosine distance, lower distance means higher relevance.
    A simple and explainable conversion is:
        similarity = 1 - distance
    """
    return 1.0 - distance


def retrieve_relevant_chunks(
    query: str,
    persist_dir: Path | None = None,
    collection_name: str | None = None,
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    top_k: int | None = None,
    min_similarity_score: float | None = None,
) -> list[RetrievedChunk]:
    """
    Retrieve relevant source chunks for a learner query.

    This service wraps the lower-level vector store query function and adds:
    - query validation
    - similarity score calculation
    - minimum relevance threshold filtering
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty.")

    persist_dir = persist_dir or Path(settings.vector_db_path)
    collection_name = collection_name or settings.collection_name
    top_k = top_k or settings.top_k
    min_similarity_score = (
        min_similarity_score
        if min_similarity_score is not None
        else settings.min_retrieval_score
    )

    raw_results = query_vector_store(
        query=query,
        persist_dir=persist_dir,
        collection_name=collection_name,
        embedding_model_name=embedding_model_name,
        top_k=top_k,
    )

    retrieved_chunks = []

    for result in raw_results:
        similarity_score = distance_to_similarity(result["distance"])

        if similarity_score < min_similarity_score:
            continue

        retrieved_chunks.append(
            RetrievedChunk(
                chunk_id=result["chunk_id"],
                source=result["source"],
                text=result["text"],
                distance=result["distance"],
                similarity_score=similarity_score,
            )
        )

    return retrieved_chunks


def format_retrieval_results(chunks: list[RetrievedChunk]) -> list[dict]:
    """
    Convert retrieved chunks into a JSON-friendly format for later API use.
    """
    return [
        {
            "rank": index + 1,
            "chunk_id": chunk.chunk_id,
            "source": chunk.source,
            "similarity_score": round(chunk.similarity_score, 4),
            "distance": round(chunk.distance, 4),
            "text_preview": chunk.text[:300],
        }
        for index, chunk in enumerate(chunks)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retrieve relevant chunks from the vector store."
    )
    parser.add_argument("--query", default="What is a variable in Python?")
    parser.add_argument("--top-k", type=int, default=settings.top_k)
    parser.add_argument(
        "--min-similarity-score",
        type=float,
        default=settings.min_retrieval_score,
    )

    args = parser.parse_args()

    chunks = retrieve_relevant_chunks(
        query=args.query,
        top_k=args.top_k,
        min_similarity_score=args.min_similarity_score,
    )

    print("Retrieval completed.")
    print(f"Query: {args.query}")
    print(f"Chunks returned: {len(chunks)}")

    for result in format_retrieval_results(chunks):
        print(f"\nRank {result['rank']}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Source: {result['source']}")
        print(f"Similarity score: {result['similarity_score']}")
        print(f"Distance: {result['distance']}")
        print(f"Text preview: {result['text_preview']}...")


if __name__ == "__main__":
    main()