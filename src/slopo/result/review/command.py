import sqlite3

from slopo.config import Config
from slopo.embedding.db import load_embeddings
from slopo.progress import ProgressReporter
from slopo.result.clustering import (
    build_clusters,
    reorder_clusters,
    filter_clusters,
)
from slopo.result.rerank import rerank_all_clusters
from slopo.result.db import load_units
from slopo.result.overlap import exclude_overlapping_pairs
from slopo.result.review.git.commands import git_diff, git_ls_untracked, git_show_prefix
from slopo.result.review.db import list_units_by_paths
from slopo.result.review.git.diff import parse_diff, parse_untracked
from slopo.result.review.index_check import verify_index_fresh
from slopo.result.identity import to_hashed_cluster
from slopo.result.models import ReviewResult
from slopo.result.review.match import match_changed_units, to_changed_file
from slopo.result.review.similarity import find_similar_pairs


def run_review(
    conn: sqlite3.Connection,
    cfg: Config,
    base_ref: str,
    log: ProgressReporter,
) -> ReviewResult | None:
    log(f"Analyzing Git changes against {base_ref}...")

    # Path prefix from Git root to source_dir, used to convert Git paths to DB paths.
    # Paths in DB are relative to source_dir, not to Git root.
    # source_dir is a subdirectory inside Git root or both are the same.
    source_dir_prefix = git_show_prefix(cfg.source_dir)

    diff_output = git_diff(base_ref, cfg.source_dir)
    untracked_output = git_ls_untracked(cfg.source_dir)

    git_changes = parse_diff(diff_output)
    git_changes.extend(parse_untracked(untracked_output))

    if not git_changes:
        log("No changes found.")
        return None

    changed_files = to_changed_file(git_changes, source_dir_prefix)

    verify_index_fresh(conn, changed_files, cfg.source_dir)

    db_paths = [cf.path_db for cf in changed_files]
    units_by_path = list_units_by_paths(conn, db_paths)
    changed_ids = set(match_changed_units(changed_files, units_by_path))

    if not changed_ids:
        log("None of the changes affect indexed code.")
        return None

    embeddings = load_embeddings(conn)
    pairs = find_similar_pairs(embeddings, changed_ids, cfg.similarity_threshold)

    if not pairs:
        log("No similar code involving the changes.")
        return None

    referenced_ids = {uid for p in pairs for uid in (p.unit_id_a, p.unit_id_b)}
    units = load_units(conn, referenced_ids)
    pairs = exclude_overlapping_pairs(pairs, units)

    if not pairs:
        log("No similar code involving the changes.")
        return None

    clusters = build_clusters(pairs)
    reranked_pairs = rerank_all_clusters(clusters, pairs, units)
    clusters = reorder_clusters(clusters, reranked_pairs)
    clusters = filter_clusters(clusters, cfg.rerank_threshold)

    if not clusters:
        log("No similar code involving the changes.")
        return None

    flagged = len({uid for c in clusters for uid in c.unit_ids} & changed_ids)
    log(f"{flagged} of {len(changed_ids)} changed units look similar to other code.")

    hashed = to_hashed_cluster(clusters, units)

    return ReviewResult(hashed, units, changed_ids)
