import sqlite3
import time

from slopo.config import Config
from slopo.embedding.db import (
    count_unembedded_units,
    load_next_batch,
    save_embeddings,
)
from slopo.embedding.embeddings import embed_units
from slopo.progress import ProgressReporter


def run_embed(
    conn: sqlite3.Connection,
    cfg: Config,
    log: ProgressReporter,
) -> None:
    total = count_unembedded_units(conn)
    if total == 0:
        log("No new code units to embed.")
        return

    log("Starting...")

    embedded = 0
    while True:
        batch = load_next_batch(
            conn, cfg.embedding_batch_size, cfg.embedding_batch_chars
        )
        if not batch:
            break
        batch_embeddings = embed_units(batch, cfg)
        with conn:
            save_embeddings(conn, batch_embeddings)
        embedded += len(batch)
        log(f"Embedded {embedded}/{total} code units...")
        if cfg.embedding_request_delay > 0:
            time.sleep(cfg.embedding_request_delay)
    log("Done")
