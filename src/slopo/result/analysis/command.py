import sqlite3

import numpy as np

from slopo.result.clustering import (
    build_clusters,
    filter_clusters,
    reorder_clusters,
)
from slopo.result.analysis.db import count_exact_copies, load_duplicate_hashes
from slopo.result.analysis.ignore import ensure_ignore_file, load_ignored
from slopo.result.identity import to_hashed_cluster
from slopo.result.rerank import rerank_all_clusters
from slopo.result.analysis.similarity import find_similar_pairs
from slopo.result.db import load_units
from slopo.result.models import AnalyzeResult, HashedCluster, UnitRecord
from slopo.result.overlap import exclude_overlapping_pairs
from slopo.config import Config
from slopo.embedding.db import load_embeddings
from slopo.progress import ProgressReporter

# Rows of the similarity matrix computed per iteration. Caps the size of
# the intermediate (block_size, n) product so it doesn't blow up at large n.
_BLOCK_SIZE = 1000


def run_analyze(
    conn: sqlite3.Connection,
    cfg: Config,
    log: ProgressReporter,
) -> AnalyzeResult | None:
    embeddings = load_embeddings(conn)

    log("Calculating similarity...")
    pairs = find_similar_pairs(embeddings, cfg.similarity_threshold, _BLOCK_SIZE)

    if not pairs:
        log("No similar code found.")
        return None

    referenced_ids = {uid for p in pairs for uid in (p.unit_id_a, p.unit_id_b)}
    units = load_units(conn, referenced_ids)
    pairs = exclude_overlapping_pairs(pairs, units)

    if not pairs:
        log("No similar code found.")
        return None

    log("Clustering and ranking...")
    clusters = build_clusters(pairs)

    reranked_pairs = rerank_all_clusters(clusters, pairs, units)
    clusters = reorder_clusters(clusters, reranked_pairs)
    clusters = filter_clusters(clusters, cfg.rerank_threshold)

    if not clusters:
        log("No similar code found.")
        return None

    hashed = to_hashed_cluster(clusters, units)

    ensure_ignore_file(cfg.ignore_file)

    ignored = load_ignored(cfg.ignore_file)
    if ignored:
        kept = [hc for hc in hashed if hc.hash not in ignored]
        ignored_count = len(hashed) - len(kept)
        hashed = kept
        if ignored_count:
            log(f"Ignored {ignored_count} previously reviewed clusters.")

    if not hashed:
        log("All similar code clusters are in the ignore list.")
        return None

    _report_ratios(conn, embeddings, hashed, units, log)

    return AnalyzeResult(hashed, units)


def _report_ratios(
    conn: sqlite3.Connection,
    embeddings: dict[int, np.ndarray],
    clusters: list[HashedCluster],
    units: dict[int, UnitRecord],
    log: ProgressReporter,
) -> None:
    duplicate_hashes = load_duplicate_hashes(conn)
    exact_copies = count_exact_copies(conn)

    flagged_with = {uid for hc in clusters for uid in hc.cluster.unit_ids}
    flagged_without = {
        uid for uid in flagged_with if units[uid].body_hash not in duplicate_hashes
    }

    total_with = len(embeddings)
    total_without = total_with - exact_copies

    log(f"Exact copies: {exact_copies} of {total_with} units.")
    log(
        "Similarity ratio (excluding exact copies):"
        f" {_ratio(len(flagged_without), total_without)}"
    )
    log(
        "Similarity ratio (including exact copies):"
        f" {_ratio(len(flagged_with), total_with)}"
    )


def _ratio(flagged: int, total: int) -> str:
    ratio = flagged / total if total > 0 else 0.0
    return f"{ratio:.2%} ({flagged}/{total} units flagged as similar)"
