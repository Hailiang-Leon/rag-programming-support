from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.backend.api import main as api_main


client = TestClient(api_main.app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "app_name" in data
    assert "environment" in data


def test_retrieve_endpoint_returns_retrieved_chunks(monkeypatch):
    fake_chunks = [
        SimpleNamespace(
            chunk_id="python_variables.txt_chunk_001",
            source="python_variables.txt",
            text="Python Variables\nA variable is a name that stores a value.",
            distance=0.2402,
            similarity_score=0.7598,
        )
    ]

    def fake_retrieve_relevant_chunks(query, top_k=None, min_similarity_score=None):
        assert query == "What is a variable in Python?"
        assert top_k == 3
        return fake_chunks

    monkeypatch.setattr(
        api_main,
        "retrieve_relevant_chunks",
        fake_retrieve_relevant_chunks,
    )

    response = client.post(
        "/retrieve",
        json={
            "query": "What is a variable in Python?",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "What is a variable in Python?"
    assert data["chunks_returned"] == 1
    assert data["results"][0]["rank"] == 1
    assert data["results"][0]["chunk_id"] == "python_variables.txt_chunk_001"
    assert data["results"][0]["source"] == "python_variables.txt"
    assert data["results"][0]["similarity_score"] == 0.7598


def test_ask_endpoint_returns_answered_response(monkeypatch):
    fake_generated_answer = object()

    def fake_generate_source_grounded_answer(
        query,
        top_k=None,
        min_similarity_score=None,
    ):
        assert query == "What is a variable in Python?"
        assert top_k == 3
        return fake_generated_answer

    def fake_generated_answer_to_dict(generated_answer):
        assert generated_answer is fake_generated_answer
        return {
            "query": "What is a variable in Python?",
            "answer_status": "answered",
            "answer": "A variable is a name that stores a value in a program [S1].",
            "sources": [
                {
                    "source_id": "S1",
                    "chunk_id": "python_variables.txt_chunk_001",
                    "source": "python_variables.txt",
                    "similarity_score": 0.7598,
                    "text_preview": "Python Variables...",
                }
            ],
        }

    monkeypatch.setattr(
        api_main,
        "generate_source_grounded_answer",
        fake_generate_source_grounded_answer,
    )
    monkeypatch.setattr(
        api_main,
        "generated_answer_to_dict",
        fake_generated_answer_to_dict,
    )

    response = client.post(
        "/ask",
        json={
            "query": "What is a variable in Python?",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "What is a variable in Python?"
    assert data["answer_status"] == "answered"
    assert "[S1]" in data["answer"]
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source"] == "python_variables.txt"


def test_ask_endpoint_returns_insufficient_evidence_response(monkeypatch):
    fake_generated_answer = object()

    def fake_generate_source_grounded_answer(
        query,
        top_k=None,
        min_similarity_score=None,
    ):
        assert query == "What will be on my final exam?"
        assert top_k == 3
        assert min_similarity_score == 0.75
        return fake_generated_answer

    def fake_generated_answer_to_dict(generated_answer):
        assert generated_answer is fake_generated_answer
        return {
            "query": "What will be on my final exam?",
            "answer_status": "insufficient_evidence",
            "answer": "I do not have enough source evidence to answer this question reliably.",
            "sources": [],
        }

    monkeypatch.setattr(
        api_main,
        "generate_source_grounded_answer",
        fake_generate_source_grounded_answer,
    )
    monkeypatch.setattr(
        api_main,
        "generated_answer_to_dict",
        fake_generated_answer_to_dict,
    )

    response = client.post(
        "/ask",
        json={
            "query": "What will be on my final exam?",
            "top_k": 3,
            "min_similarity_score": 0.75,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "What will be on my final exam?"
    assert data["answer_status"] == "insufficient_evidence"
    assert data["sources"] == []
    assert "not have enough source evidence" in data["answer"]


def test_ask_endpoint_rejects_empty_query():
    response = client.post(
        "/ask",
        json={
            "query": "",
            "top_k": 3,
        },
    )

    assert response.status_code == 422
