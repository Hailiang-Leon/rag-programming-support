from __future__ import annotations

import argparse
from dataclasses import dataclass

from src.backend.rag.ollama_client import generate_with_ollama
from src.backend.rag.retriever import RetrievedChunk, retrieve_relevant_chunks


INSUFFICIENT_EVIDENCE_MESSAGE = (
    "I do not have enough source evidence to answer this question reliably."
)


@dataclass
class SourceCitation:
    source_id: str
    chunk_id: str
    source: str
    similarity_score: float
    text_preview: str


@dataclass
class GeneratedAnswer:
    query: str
    answer_status: str
    answer: str
    sources: list[SourceCitation]


def build_sources(chunks: list[RetrievedChunk]) -> list[SourceCitation]:
    """
    Convert retrieved chunks into source metadata for answer output.
    """
    sources: list[SourceCitation] = []

    for index, chunk in enumerate(chunks):
        sources.append(
            SourceCitation(
                source_id=f"S{index + 1}",
                chunk_id=chunk.chunk_id,
                source=chunk.source,
                similarity_score=round(chunk.similarity_score, 4),
                text_preview=chunk.text[:300],
            )
        )

    return sources


def build_grounded_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    """
    Build a source-grounded prompt using the learner query and retrieved chunks.
    """
    source_blocks = []

    for index, chunk in enumerate(chunks):
        source_blocks.append(
            f"[S{index + 1}]\n"
            f"Source file: {chunk.source}\n"
            f"Chunk ID: {chunk.chunk_id}\n"
            f"Content:\n{chunk.text}"
        )

    sources_text = "\n\n".join(source_blocks)

    return f"""
You are a source-grounded programming learning assistant for beginner Python learners.

Answer the learner's question using ONLY the provided sources.
Do not use outside knowledge.
If the provided sources are not enough, say that there is not enough source evidence.
Use beginner-friendly language.
Prefer explanation over simply giving code.
When you use information from a source, cite it using [S1], [S2], etc.

Learner question:
{query}

Provided sources:
{sources_text}

Write a clear, concise answer grounded in the provided sources.
""".strip()


def generate_source_grounded_answer(
    query: str,
    top_k: int | None = None,
    min_similarity_score: float | None = None,
) -> GeneratedAnswer:
    """
    Retrieve relevant chunks and generate a source-grounded answer using Ollama.
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty.")

    chunks = retrieve_relevant_chunks(
        query=query,
        top_k=top_k,
        min_similarity_score=min_similarity_score,
    )

    if not chunks:
        return GeneratedAnswer(
            query=query,
            answer_status="insufficient_evidence",
            answer=INSUFFICIENT_EVIDENCE_MESSAGE,
            sources=[],
        )

    prompt = build_grounded_prompt(query=query, chunks=chunks)
    answer = generate_with_ollama(prompt=prompt)
    sources = build_sources(chunks)

    return GeneratedAnswer(
        query=query,
        answer_status="answered",
        answer=answer,
        sources=sources,
    )


def generated_answer_to_dict(generated_answer: GeneratedAnswer) -> dict:
    """
    Convert GeneratedAnswer into a JSON-friendly dictionary.
    """
    return {
        "query": generated_answer.query,
        "answer_status": generated_answer.answer_status,
        "answer": generated_answer.answer,
        "sources": [
            {
                "source_id": source.source_id,
                "chunk_id": source.chunk_id,
                "source": source.source,
                "similarity_score": source.similarity_score,
                "text_preview": source.text_preview,
            }
            for source in generated_answer.sources
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a source-grounded answer using retrieval and Ollama."
    )
    parser.add_argument("--query", default="What is a variable in Python?")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-similarity-score", type=float, default=None)

    args = parser.parse_args()

    generated_answer = generate_source_grounded_answer(
        query=args.query,
        top_k=args.top_k,
        min_similarity_score=args.min_similarity_score,
    )

    result = generated_answer_to_dict(generated_answer)

    print("Answer generation completed.")
    print(f"Query: {result['query']}")
    print(f"Answer status: {result['answer_status']}")
    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")
    for source in result["sources"]:
        print(
            f"{source['source_id']} | {source['source']} | "
            f"{source['chunk_id']} | similarity={source['similarity_score']}"
        )


if __name__ == "__main__":
    main()
