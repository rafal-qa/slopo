import sqlite3

from slopo.result.analysis.db import count_exact_copies, load_duplicate_hashes

_SETUP = """
    INSERT INTO files (id, path, mtime) VALUES (1, 'File.java', 0);
    INSERT INTO code_units (id, file_id, name, body, start_line, end_line, body_node_count, body_hash)
        VALUES (1, 1, 'a', 'body-a', 1, 2, 3, 'dup'),
               (2, 1, 'b', 'body-b', 1, 2, 3, 'dup'),
               (3, 1, 'c', 'body-c', 1, 2, 3, 'dup'),
               (4, 1, 'd', 'body-d', 1, 2, 3, 'unique');
"""


def test_counts_every_member_of_a_duplicate_group(conn: sqlite3.Connection):
    conn.executescript(_SETUP)

    assert count_exact_copies(conn) == 3


def test_counts_zero_when_all_units_unique(conn: sqlite3.Connection):
    conn.executescript("""
        INSERT INTO files (id, path, mtime) VALUES (1, 'File.java', 0);
        INSERT INTO code_units (id, file_id, name, body, start_line, end_line, body_node_count, body_hash)
            VALUES (1, 1, 'a', 'a', 1, 2, 3, 'x'),
                   (2, 1, 'b', 'b', 1, 2, 3, 'y');
    """)

    assert count_exact_copies(conn) == 0


def test_returns_only_hashes_shared_by_more_than_one_unit(conn: sqlite3.Connection):
    conn.executescript(_SETUP)

    assert load_duplicate_hashes(conn) == {"dup"}
