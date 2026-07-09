from __future__ import annotations

import sqlite3
from pathlib import Path


DEFAULT_DATABASE_PATH = Path("data/evaluation/query_logs.sqlite3")


QUERY_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS query_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    answer_status TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def get_database_connection(
    database_path: str | Path | None = None,
) -> sqlite3.Connection:
    """
    Create a SQLite database connection and ensure the parent directory exists.
    """
    db_path = Path(database_path) if database_path else DEFAULT_DATABASE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialise_database(
    database_path: str | Path | None = None,
) -> None:
    """
    Initialise the SQLite database tables required by the application.
    """
    with get_database_connection(database_path) as connection:
        connection.execute(QUERY_LOG_SCHEMA)
        connection.commit()
