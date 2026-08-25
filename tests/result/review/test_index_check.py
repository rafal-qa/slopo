import os
import sqlite3
from pathlib import Path

import pytest

from slopo.result.review.index_check import StaleIndexError, verify_index_fresh
from slopo.result.review.models import ChangedFile

_SETUP = """
    INSERT INTO files (id, path, mtime)
        VALUES (1, 'Foo.java', 100.0),
               (2, 'Bar.java', 200.0);
"""


def test_passes_when_no_changed_files(conn: sqlite3.Connection, tmp_path: Path):
    conn.executescript(_SETUP)

    verify_index_fresh(conn, [], tmp_path)


def test_passes_when_disk_mtime_matches_db_mtime(
    conn: sqlite3.Connection, tmp_path: Path
):
    conn.executescript(_SETUP)
    path = tmp_path / "Foo.java"
    path.write_text("")
    os.utime(path, (100.0, 100.0))

    verify_index_fresh(
        conn,
        [ChangedFile(path_db="Foo.java", is_new=False, changed_ranges=[])],
        tmp_path,
    )


def test_raises_when_disk_mtime_differs_from_db_mtime(
    conn: sqlite3.Connection, tmp_path: Path
):
    conn.executescript(_SETUP)
    path = tmp_path / "Foo.java"
    path.write_text("")
    os.utime(path, (999.0, 999.0))

    with pytest.raises(StaleIndexError):
        verify_index_fresh(
            conn,
            [ChangedFile(path_db="Foo.java", is_new=False, changed_ranges=[])],
            tmp_path,
        )


def test_ignores_changed_files_not_in_index(conn: sqlite3.Connection, tmp_path: Path):
    conn.executescript(_SETUP)
    path = tmp_path / "NewFile.java"
    path.write_text("")
    os.utime(path, (500.0, 500.0))

    verify_index_fresh(
        conn,
        [ChangedFile(path_db="NewFile.java", is_new=True, changed_ranges=[])],
        tmp_path,
    )


def test_ignores_indexed_files_missing_from_disk(
    conn: sqlite3.Connection, tmp_path: Path
):
    conn.executescript(_SETUP)

    verify_index_fresh(
        conn,
        [ChangedFile(path_db="Foo.java", is_new=False, changed_ranges=[])],
        tmp_path,
    )


def test_raises_when_any_of_multiple_files_is_stale(
    conn: sqlite3.Connection, tmp_path: Path
):
    conn.executescript(_SETUP)

    foo = tmp_path / "Foo.java"
    foo.write_text("")
    os.utime(foo, (100.0, 100.0))

    bar = tmp_path / "Bar.java"
    bar.write_text("")
    os.utime(bar, (999.0, 999.0))

    with pytest.raises(StaleIndexError):
        verify_index_fresh(
            conn,
            [
                ChangedFile(path_db="Foo.java", is_new=False, changed_ranges=[]),
                ChangedFile(path_db="Bar.java", is_new=False, changed_ranges=[]),
            ],
            tmp_path,
        )
