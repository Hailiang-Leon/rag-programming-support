from fastapi.testclient import TestClient

from src.backend.api import main as api_main


client = TestClient(api_main.app)


def test_ask_endpoint_saves_query_log(monkeypatch):
    fake_generated_answer = object()
    saved_logs = []

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
            "answer": "A variable is a name that stores a value [S1].",
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

    def fake_save_query_log(query, answer_status, answer, sources):
        saved_logs.append(
            {
                "query": query,
                "answer_status": answer_status,
                "answer": answer,
                "sources": sources,
            }
        )
        return 1

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
    monkeypatch.setattr(
        api_main,
        "save_query_log",
        fake_save_query_log,
    )

    response = client.post(
        "/ask",
        json={
            "query": "What is a variable in Python?",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    assert len(saved_logs) == 1

    saved_log = saved_logs[0]

    assert saved_log["query"] == "What is a variable in Python?"
    assert saved_log["answer_status"] == "answered"
    assert saved_log["answer"] == "A variable is a name that stores a value [S1]."
    assert saved_log["sources"][0]["source"] == "python_variables.txt"
