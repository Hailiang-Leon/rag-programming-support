from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.backend.api import main as api_main
from src.backend.storage.query_log_repository import (
    list_query_logs,
    save_query_log,
)


client = TestClient(api_main.app)


@pytest.mark.parametrize("top_k", [0, 11])
def test_retrieve_rejects_invalid_top_k(top_k):
    response = client.post(
        "/retrieve",
        json={
            "query": "What is a variable in Python?",
            "top_k": top_k,
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "min_similarity_score",
    [-0.01, 1.01],
)
def test_ask_rejects_invalid_similarity_score(
    min_similarity_score,
):
    response = client.post(
        "/ask",
        json={
            "query": "What is a variable in Python?",
            "min_similarity_score": min_similarity_score,
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize("hint_level", [0, 4])
def test_ask_rejects_invalid_hint_level(hint_level):
    response = client.post(
        "/ask",
        json={
            "query": "Give me a hint about Python loops.",
            "response_mode": "hint",
            "hint_level": hint_level,
        },
    )

    assert response.status_code == 422


def test_sql_injection_like_query_is_stored_as_plain_text(
    tmp_path,
):
    database_path = tmp_path / "security_test.sqlite3"
    malicious_query = (
        "'; DROP TABLE query_logs; --"
    )

    save_query_log(
        query=malicious_query,
        answer_status="insufficient_evidence",
        answer="The query was handled as ordinary text.",
        sources=[],
        database_path=database_path,
    )

    logs = list_query_logs(
        limit=10,
        database_path=database_path,
    )

    assert len(logs) == 1
    assert logs[0]["query"] == malicious_query

    # A second insert confirms that the table still exists.
    save_query_log(
        query="What is a Python variable?",
        answer_status="answered",
        answer="A variable stores a value.",
        sources=[],
        database_path=database_path,
    )

    updated_logs = list_query_logs(
        limit=10,
        database_path=database_path,
    )

    assert len(updated_logs) == 2
    assert (
        updated_logs[0]["query"]
        == "What is a Python variable?"
    )


def test_frontend_uses_safe_text_rendering():
    app_js_path = Path("src/frontend/app.js")
    app_js = app_js_path.read_text(encoding="utf-8")

    assert "innerHTML" not in app_js
    assert "createTextNode" in app_js
    assert "textContent" in app_js
