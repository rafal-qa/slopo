import sqlite3
from dataclasses import dataclass

from slopo.db import chunked
from slopo.indexing.parsing.base import CodeUnit


@dataclass
class IndexedFile:
    id: int
    mtime: float


def list_indexed_files(conn: sqlite3.Connection) -> dict[str, IndexedFile]:
    rows = conn.execute("SELECT path, id, mtime FROM files").fetchall()
    return {row[0]: IndexedFile(id=row[1], mtime=row[2]) for row in rows}


def delete_files(conn: sqlite3.Connection, file_ids: list[int]) -> None:
    for chunk in chunked(file_ids):
        id_placeholders = ",".join("?" * len(chunk))
        conn.execute(
            f"DELETE FROM code_units WHERE file_id IN ({id_placeholders})", chunk
        )
        conn.execute(f"DELETE FROM files WHERE id IN ({id_placeholders})", chunk)


def insert_file(conn: sqlite3.Connection, path: str, mtime: float) -> int:
    conn.execute("INSERT INTO files (path, mtime) VALUES (?, ?)", (path, mtime))
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_file_mtime(conn: sqlite3.Connection, file_id: int, mtime: float) -> None:
    conn.execute("UPDATE files SET mtime = ? WHERE id = ?", (mtime, file_id))


def delete_file_units(conn: sqlite3.Connection, file_id: int) -> None:
    conn.execute("DELETE FROM code_units WHERE file_id = ?", (file_id,))


def prune_orphan_embeddings(conn: sqlite3.Connection) -> None:
    conn.execute(
        "DELETE FROM embeddings"
        " WHERE body_hash NOT IN (SELECT body_hash FROM code_units)"
    )


def insert_file_units(
    conn: sqlite3.Connection, file_id: int, units: list[CodeUnit]
) -> None:
    conn.executemany(
        "INSERT INTO code_units"
        " (file_id, name, body, start_line, end_line, body_node_count, body_hash)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                file_id,
                u.name,
                u.body,
                u.start_line,
                u.end_line,
                u.body_node_count,
                u.body_hash,
            )
            for u in units
        ],
    )
