import pytest

from slopo.result import boost
from slopo.result.models import Cluster, SimilarPair, UnitRecord
from slopo.result.rerank import (
    path_hops,
    rerank_all_clusters,
    rerank_cluster_pairs,
    rerank_pair_score,
)


def pair(a: int, b: int, sim: float) -> SimilarPair:
    return SimilarPair(similarity=sim, unit_id_a=a, unit_id_b=b)


def unit(path: str, start: int = 1, end: int = 10) -> UnitRecord:
    return UnitRecord(
        unit_id=0,
        file_path=path,
        name="",
        start_line=start,
        end_line=end,
        body="",
        body_hash="",
    )


# --- path_hops ---


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("a/X.java", "a/Y.java", 0),
        ("a/b/X.java", "a/Y.java", 1),
        ("a/b/X.java", "a/c/Y.java", 2),
        ("a/b/X.java", "c/Y.java", 3),
        ("a/b/X.java", "c/d/Y.java", 4),
        ("X.java", "Y.java", 0),
        ("a/b/c/X.java", "a/b/c/Y.java", 0),
    ],
)
def test_path_hops(a: str, b: str, expected: int):
    assert path_hops(a, b) == expected
    assert path_hops(b, a) == expected


# --- rerank_pair_score ---


def test_pair_score_applies_cross_dir_boost_for_different_directories():
    expected_boost = boost.cross_dir(path_hops("a/X.java", "b/Y.java"))
    score = rerank_pair_score(pair(1, 2, 0.8), unit("a/X.java"), unit("b/Y.java"))
    assert score == pytest.approx(0.8 * (1 + expected_boost))


def test_pair_score_applies_same_file_boost_for_same_file():
    expected_boost = boost.same_file(line_distance=300)
    score = rerank_pair_score(
        pair(1, 2, 0.95),
        unit("a/X.java", start=1, end=10),
        unit("a/X.java", start=310, end=320),
    )
    assert score == pytest.approx(0.95 * (1 + expected_boost))


def test_pair_score_no_boost_for_same_directory():
    score = rerank_pair_score(pair(1, 2, 0.9), unit("a/X.java"), unit("a/Y.java"))
    assert score == pytest.approx(0.9)


# --- rerank_cluster_pairs ---


def test_cluster_pairs_applies_each_boost_by_pair_relationship():
    units = {
        1: unit("a/X.java", start=1, end=10),
        2: unit("a/X.java", start=310, end=320),  # same file as 1, 300 lines away
        3: unit("b/Y.java"),  # cross dir
    }
    pairs = [pair(1, 2, 0.9), pair(1, 3, 0.85), pair(2, 3, 0.8)]

    same_file_boost = boost.same_file(line_distance=300)
    cross_dir_boost = boost.cross_dir(path_hops("a/X.java", "b/Y.java"))

    assert rerank_cluster_pairs(pairs, units) == [
        pair(1, 2, 0.9 * (1 + same_file_boost)),
        pair(1, 3, 0.85 * (1 + cross_dir_boost)),
        pair(2, 3, 0.8 * (1 + cross_dir_boost)),
    ]


# --- rerank_all_clusters ---


def test_all_clusters_processes_each_cluster_independently():
    clusters = [
        Cluster(unit_ids=[1, 2], min_similarity=0.9, max_similarity=0.9),
        Cluster(unit_ids=[3, 4], min_similarity=0.85, max_similarity=0.85),
    ]
    units = {
        1: unit("a/X.java"),
        2: unit("b/Y.java"),  # cross dir
        3: unit("c/X.java"),
        4: unit("c/Y.java"),  # same dir -> no boost
    }
    pairs = [pair(1, 2, 0.9), pair(3, 4, 0.85)]

    cross_dir_boost = boost.cross_dir(path_hops("a/X.java", "b/Y.java"))

    assert rerank_all_clusters(clusters, pairs, units) == [
        pair(1, 2, 0.9 * (1 + cross_dir_boost)),
        pair(3, 4, 0.85),
    ]
