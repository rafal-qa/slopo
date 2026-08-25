import sqlite3

from slopo.result.review.db import list_units_by_paths
from slopo.result.review.models import UnitRange

_SETUP = """
    INSERT INTO files (id, path, mtime)
        VALUES (1, 'src/Foo.java', 0),
               (2, 'src/Bar.java', 0);
    INSERT INTO code_units (id, file_id, name, body, start_line, end_line, body_node_count, body_hash)
        VALUES (1, 1, 'a', 'body-a', 1, 5, 3, 'h1'),
               (2, 1, 'b', 'body-b', 10, 20, 3, 'h2'),
               (3, 2, 'c', 'body-c', 3, 7, 3, 'h3');
"""


def test_returns_empty_dict_for_no_matching_paths(conn: sqlite3.Connection):
    conn.executescript(_SETUP)

    assert list_units_by_paths(conn, ["no/such/file.java"]) == {}


def test_returns_units_grouped_by_file_path(conn: sqlite3.Connection):
    conn.executescript(_SETUP)

    result = list_units_by_paths(conn, ["src/Foo.java", "src/Bar.java"])

    assert result == {
        "src/Foo.java": [
            UnitRange(id=1, start_line=1, end_line=5),
            UnitRange(id=2, start_line=10, end_line=20),
        ],
        "src/Bar.java": [
            UnitRange(id=3, start_line=3, end_line=7),
        ],
    }


def test_excludes_files_not_in_requested_paths(conn: sqlite3.Connection):
    conn.executescript(_SETUP)

    result = list_units_by_paths(conn, ["src/Foo.java"])

    assert result.keys() == {"src/Foo.java"}
