import sqlite3
from pathlib import Path

from slopo.result.review.db import load_mtimes_by_paths
from slopo.result.review.models import ChangedFile


class StaleIndexError(Exception):
    pass


def verify_index_fresh(
    conn: sqlite3.Connection,
    changed_files: list[ChangedFile],
    source_dir: Path,
) -> None:
    db_mtimes = load_mtimes_by_paths(conn, [cf.path_db for cf in changed_files])
    for cf in changed_files:
        db_mtime = db_mtimes.get(cf.path_db)
        if db_mtime is None:
            continue
        disk_path = source_dir / cf.path_db
        if not disk_path.is_file():
            continue
        if db_mtime != disk_path.stat().st_mtime:
            raise StaleIndexError
