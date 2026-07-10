from pathlib import Path

import pytest

from src.backend.rag import retriever
from src.backend.rag.retriever import RetrievedChunk


def test_distance_to_similarity():
    assert retriever.distance_to_similarity(0.0) == 1.0
    assert retriever.distance_to_similarity(0.25) == 0.75
    assert retriever.distance_to_similarity(1.0) == 0.0


def test_retrieve_relevant_chunks_rejects_empty_query():
    with pytest.raises(ValueError, match="query must not be empty"):
        retriever.retrieve_relevant_chunks(query="")

    with pytest.raises(ValueError, match="query must not be empty"):
        retriever.retrieve_relevant_chunks(query="   ")


def test_retrieve_relevant_chunks_converts_and_filters_results(
    monkeypatch,
    tmp_path,
):
    captured_arguments = {}

    def fake_query_vector_store(
        query,
        persist_dir,
        collection_name,
        embedding_model_name,
        top_k,
    ):
        captured_arguments["query"] = query
        captured_arguments["persist_dir"] = persist_dir
        captured_arguments["collection_name"] = collection_name
        captured_arguments["embedding_model_name"] = embedding_model_name
        captured_arguments["top_k"] = top_k

        return [
            {
                "chunk_id": "python_variables.txt_chunk_001",
                "source": "python_variables.txt",
                "text": "A variable is a name used to store a value.",
                "distance": 0.20,
            },
            {
                "chunk_id": "python_functions.txt_chunk_001",
                "source": "python_functions.txt",
                "text": "A function is a reusable block of code.",
                "distance": 0.70,
            },
        ]

    monkeypatch.setattr(
        retriever,
        "query_vector_store",
        fake_query_vector_store,
    )

    persist_dir = tmp_path / "test_chroma"

    chunks = retriever.retrieve_relevant_chunks(
        query="What is a variable in Python?",
        persist_dir=persist_dir,
        collection_name="test_collection",
        embedding_model_name="test_embedding_model",
        top_k=2,
        min_similarity_score=0.50,
    )

    assert captured_arguments["query"] == "What is a variable in Python?"
    assert captured_arguments["persist_dir"] == persist_dir
    assert captured_arguments["collection_name"] == "test_collection"
    assert captured_arguments["embedding_model_name"] == "test_embedding_model"
    assert captured_arguments["top_k"] == 2

    assert len(chunks) == 1

    chunk = chunks[0]

    assert isinstance(chunk, RetrievedChunk)
    assert chunk.chunk_id == "python_variables.txt_chunk_001"
    assert chunk.source == "python_variables.txt"
    assert chunk.text == "A variable is a name used to store a value."
    assert chunk.distance == 0.20
    assert chunk.similarity_score == pytest.approx(0.80)


def test_retrieve_relevant_chunks_includes_threshold_boundary(
    monkeypatch,
    tmp_path,
):
    def fake_query_vector_store(
        query,
        persist_dir,
        collection_name,
        embedding_model_name,
        top_k,
    ):
        return [
            {
                "chunk_id": "python_loops.txt_chunk_001",
                "source": "python_loops.txt",
                "text": "A loop repeats a block of code.",
                "distance": 0.40,
            }
        ]

    monkeypatch.setattr(
        retriever,
        "query_vector_store",
        fake_query_vector_store,
    )

    chunks = retriever.retrieve_relevant_chunks(
        query="What is a loop?",
        persist_dir=tmp_path / "test_chroma",
        collection_name="test_collection",
        top_k=1,
        min_similarity_score=0.60,
    )

    assert len(chunks) == 1
    assert chunks[0].similarity_score == pytest.approx(0.60)


def test_format_retrieval_results_returns_api_friendly_structure():
    long_text = "A" * 350

    chunks = [
        RetrievedChunk(
            chunk_id="python_variables.txt_chunk_001",
            source="python_variables.txt",
            text=long_text,
            distance=0.24024,
            similarity_score=0.75976,
        ),
        RetrievedChunk(
            chunk_id="python_functions.txt_chunk_001",
            source="python_functions.txt",
            text="A function is a reusable block of code.",
            distance=0.35111,
            similarity_score=0.64889,
        ),
    ]

    formatted = retriever.format_retrieval_results(chunks)

    assert len(formatted) == 2

    assert formatted[0]["rank"] == 1
    assert formatted[0]["chunk_id"] == "python_variables.txt_chunk_001"
    assert formatted[0]["source"] == "python_variables.txt"
    assert formatted[0]["distance"] == 0.2402
    assert formatted[0]["similarity_score"] == 0.7598
    assert len(formatted[0]["text_preview"]) == 300

    assert formatted[1]["rank"] == 2
    assert formatted[1]["chunk_id"] == "python_functions.txt_chunk_001"
    assert formatted[1]["source"] == "python_functions.txt"
