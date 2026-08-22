import sqlite3
from dataclasses import dataclass
from pathlib import Path

from slopo.indexing.db import (
    delete_file_units,
    delete_files,
    insert_file,
    insert_file_units,
    list_indexed_files,
    prune_orphan_embeddings,
    update_file_mtime,
    IndexedFile,
)
from slopo.indexing.scanner import filter_units, parse_file, scan_directory


@dataclass
class SyncStats:
    indexed_files: int
    skipped_files: int
    indexed_units: int
    removed_files: int


def sync_index(
    conn: sqlite3.Connection,
    directory: Path,
    body_node_count_threshold: int,
    exclude: list[str],
) -> SyncStats:
    indexed_files = 0
    skipped_files = 0
    indexed_units = 0

    indexed: dict[str, IndexedFile] = list_indexed_files(conn)
    seen_paths: set[str] = set()

    for path_str in scan_directory(directory, exclude):
        seen_paths.add(path_str)
        full_path: Path = directory / path_str
        mtime = full_path.stat().st_mtime
        existing = indexed.get(path_str)

        if existing is not None and existing.mtime == mtime:
            skipped_files += 1
            continue

        units = parse_file(full_path)
        units = filter_units(units, body_node_count_threshold)

        if existing is None:
            file_id = insert_file(conn, path_str, mtime)
        else:
            update_file_mtime(conn, existing.id, mtime)
            file_id = existing.id
            delete_file_units(conn, file_id)

        insert_file_units(conn, file_id, units)
        indexed_files += 1
        indexed_units += len(units)

    removed_ids = []
    for path, indexed_file in indexed.items():
        if path not in seen_paths:
            removed_ids.append(indexed_file.id)
    delete_files(conn, removed_ids)

    prune_orphan_embeddings(conn)

    return SyncStats(
        indexed_files=indexed_files,
        skipped_files=skipped_files,
        indexed_units=indexed_units,
        removed_files=len(removed_ids),
    )
