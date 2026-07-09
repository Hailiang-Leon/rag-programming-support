from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.backend.storage.database import get_database_connection, initialise_database


def save_query_log(
    query: str,
    answer_status: str,
    answer: str,
    sources: list[dict[str, Any]],
    database_path: str | Path | None = None,
) -> int:
    """
    Save a query and generated answer to the SQLite query log.
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty.")

    if not answer_status or not answer_status.strip():
        raise ValueError("answer_status must not be empty.")

    if answer is None:
        raise ValueError("answer must not be None.")

    initialise_database(database_path)

    sources_json = json.dumps(sources, ensure_ascii=False)
    created_at = datetime.now(timezone.utc).isoformat()

    with get_database_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO query_logs (
                query,
                answer_status,
                answer,
                sources_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                query,
                answer_status,
                answer,
                sources_json,
                created_at,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)


def list_query_logs(
    limit: int = 20,
    database_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """
    Return recent query logs from the SQLite database.
    """
    if limit < 1:
        raise ValueError("limit must be greater than 0.")

    initialise_database(database_path)

    with get_database_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                query,
                answer_status,
                answer,
                sources_json,
                created_at
            FROM query_logs
            ORDER BY id DESC
            LIMIT ?;
            """,
            (limit,),
        ).fetchall()

    logs: list[dict[str, Any]] = []

    for row in rows:
        log = dict(row)
        log["sources"] = json.loads(log.pop("sources_json"))
        logs.append(log)

    return logs
