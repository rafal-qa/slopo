import sqlite3

from slopo.db import chunked
from slopo.result.review.models import UnitRange


def list_units_by_paths(
    conn: sqlite3.Connection, paths: list[str]
) -> dict[str, list[UnitRange]]:
    result: dict[str, list[UnitRange]] = {}
    for chunk in chunked(paths):
        placeholders = ",".join("?" * len(chunk))
        rows = conn.execute(
            "SELECT f.path, cu.id, cu.start_line, cu.end_line"
            " FROM code_units cu"
            " JOIN files f ON cu.file_id = f.id"
            f" WHERE f.path IN ({placeholders})",
            chunk,
        ).fetchall()
        for path, unit_id, start_line, end_line in rows:
            if path not in result:
                result[path] = []
            result[path].append(
                UnitRange(id=unit_id, start_line=start_line, end_line=end_line)
            )
    return result


def load_mtimes_by_paths(
    conn: sqlite3.Connection, paths: list[str]
) -> dict[str, float]:
    result: dict[str, float] = {}
    for chunk in chunked(paths):
        placeholders = ",".join("?" * len(chunk))
        rows = conn.execute(
            f"SELECT path, mtime FROM files WHERE path IN ({placeholders})",
            chunk,
        ).fetchall()
        for path, mtime in rows:
            result[path] = mtime
    return result
