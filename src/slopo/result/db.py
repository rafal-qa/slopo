import sqlite3

from slopo.result.models import UnitRecord
from slopo.db import chunked


def load_units(conn: sqlite3.Connection, unit_ids: set[int]) -> dict[int, UnitRecord]:
    units: dict[int, UnitRecord] = {}
    for chunk in chunked(list(unit_ids)):
        id_placeholders = ",".join("?" * len(chunk))
        rows = conn.execute(
            f"""
            SELECT cu.id, f.path, cu.name, cu.start_line, cu.end_line, cu.body, cu.body_hash
            FROM code_units cu
            JOIN files f ON f.id = cu.file_id
            WHERE cu.id IN ({id_placeholders})
            """,
            chunk,
        ).fetchall()
        for row in rows:
            units[row[0]] = UnitRecord(
                unit_id=row[0],
                file_path=row[1],
                name=row[2],
                start_line=row[3],
                end_line=row[4],
                body=row[5],
                body_hash=row[6],
            )
    return units
