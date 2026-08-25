import sqlite3


def count_exact_copies(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) FROM code_units
        WHERE body_hash IN (
            SELECT body_hash FROM code_units
            GROUP BY body_hash HAVING COUNT(*) > 1
        )
        """
    ).fetchone()
    return row[0]


def load_duplicate_hashes(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        """
        SELECT body_hash FROM code_units
        GROUP BY body_hash HAVING COUNT(*) > 1
        """
    ).fetchall()
    return {row[0] for row in rows}
