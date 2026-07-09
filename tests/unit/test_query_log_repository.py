from src.backend.storage.query_log_repository import list_query_logs, save_query_log


def test_save_query_log_creates_log_entry(tmp_path):
    database_path = tmp_path / "query_logs.sqlite3"

    log_id = save_query_log(
        query="What is a variable in Python?",
        answer_status="answered",
        answer="A variable is a name that stores a value [S1].",
        sources=[
            {
                "source_id": "S1",
                "chunk_id": "python_variables.txt_chunk_001",
                "source": "python_variables.txt",
                "similarity_score": 0.7598,
                "text_preview": "Python Variables...",
            }
        ],
        database_path=database_path,
    )

    logs = list_query_logs(database_path=database_path)

    assert log_id == 1
    assert len(logs) == 1
    assert logs[0]["query"] == "What is a variable in Python?"
    assert logs[0]["answer_status"] == "answered"
    assert logs[0]["answer"] == "A variable is a name that stores a value [S1]."
    assert logs[0]["sources"][0]["source_id"] == "S1"
    assert logs[0]["sources"][0]["source"] == "python_variables.txt"
    assert "created_at" in logs[0]


def test_list_query_logs_returns_most_recent_first(tmp_path):
    database_path = tmp_path / "query_logs.sqlite3"

    save_query_log(
        query="First query",
        answer_status="answered",
        answer="First answer",
        sources=[],
        database_path=database_path,
    )
    save_query_log(
        query="Second query",
        answer_status="insufficient_evidence",
        answer="Second answer",
        sources=[],
        database_path=database_path,
    )

    logs = list_query_logs(database_path=database_path)

    assert len(logs) == 2
    assert logs[0]["query"] == "Second query"
    assert logs[1]["query"] == "First query"


def test_save_query_log_rejects_empty_query(tmp_path):
    database_path = tmp_path / "query_logs.sqlite3"

    try:
        save_query_log(
            query="",
            answer_status="answered",
            answer="Answer",
            sources=[],
            database_path=database_path,
        )
    except ValueError as error:
        assert "query must not be empty" in str(error)
    else:
        raise AssertionError("Expected ValueError for empty query.")
