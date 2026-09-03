import sqlite3
from collections.abc import Iterator, Sequence
from pathlib import Path

from slopo.config import Config
from slopo.schema import SCHEMA_VERSION, create_schema

# Stay under the 999 SQLITE_MAX_VARIABLE_NUMBER default of pre-3.32 SQLite,
# leaving headroom for other bound parameters in the same statement.
_MAX_SQL_VARIABLES = 900


class DatabaseNotFoundError(Exception):
    def __init__(self, db_file: Path) -> None:
        self.db_file = db_file


class ConfigurationMismatchError(Exception):
    def __init__(self, field: str, stored: str, current: str) -> None:
        self.field = field
        self.stored = stored
        self.current = current


class SchemaVersionMismatchError(Exception):
    def __init__(self, database_version: int, expected_version: int) -> None:
        self.database_version = database_version
        self.expected_version = expected_version


def open_db(cfg: Config) -> sqlite3.Connection:
    if not cfg.db_file.exists():
        raise DatabaseNotFoundError(cfg.db_file)
    conn = _connect(cfg.db_file)
    _check_schema_version(conn)
    _check_metadata(conn, cfg)
    return conn


def create_db(cfg: Config) -> sqlite3.Connection:
    conn = _connect(cfg.db_file)
    create_schema(conn)
    conn.execute(
        "INSERT INTO metadata"
        " (id, source_dir, embedding_model, embedding_dimensions, body_node_count_threshold)"
        " VALUES (1, ?, ?, ?, ?)",
        (
            str(cfg.source_dir.resolve()),
            cfg.embedding_model,
            cfg.embedding_dimensions,
            cfg.body_node_count_threshold,
        ),
    )
    conn.commit()
    return conn


def chunked[T](values: Sequence[T]) -> Iterator[list[T]]:
    for start in range(0, len(values), _MAX_SQL_VARIABLES):
        yield list(values[start : start + _MAX_SQL_VARIABLES])


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _check_schema_version(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT version FROM schema_version").fetchone()
    if row[0] != SCHEMA_VERSION:
        raise SchemaVersionMismatchError(
            database_version=row[0], expected_version=SCHEMA_VERSION
        )


def _check_metadata(conn: sqlite3.Connection, cfg: Config) -> None:
    stored = conn.execute(
        "SELECT source_dir, embedding_model, embedding_dimensions, body_node_count_threshold"
        " FROM metadata WHERE id = 1"
    ).fetchone()

    if stored is None:
        raise sqlite3.OperationalError

    resolved_source_dir = str(cfg.source_dir.resolve())
    if stored[0] != resolved_source_dir:
        raise ConfigurationMismatchError("source_dir", stored[0], resolved_source_dir)
    if stored[1] != cfg.embedding_model:
        raise ConfigurationMismatchError(
            "embedding_model", stored[1], cfg.embedding_model
        )
    if stored[2] != cfg.embedding_dimensions:
        raise ConfigurationMismatchError(
            "embedding_dimensions", str(stored[2]), str(cfg.embedding_dimensions)
        )
    if stored[3] != cfg.body_node_count_threshold:
        raise ConfigurationMismatchError(
            "body_node_count_threshold",
            str(stored[3]),
            str(cfg.body_node_count_threshold),
        )
