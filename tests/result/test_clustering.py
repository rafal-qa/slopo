from slopo.result.clustering import (
    build_clusters,
    cluster_pairs,
    filter_clusters,
    reorder_clusters,
    sort_cluster,
)
from slopo.result.models import Cluster, SimilarPair


def pair(a: int, b: int, sim: float) -> SimilarPair:
    return SimilarPair(similarity=sim, unit_id_a=a, unit_id_b=b)


# --- cluster_pairs ---


def test_two_connected_pairs_form_one_cluster():
    pairs = [pair(1, 2, 0.9), pair(2, 3, 0.8)]
    assert cluster_pairs(pairs) == [{1, 2, 3}]


def test_disconnected_pairs_form_separate_clusters():
    pairs = [pair(1, 2, 0.9), pair(3, 4, 0.8)]
    assert cluster_pairs(pairs) == [{1, 2}, {3, 4}]


def test_single_pair_forms_one_cluster():
    pairs = [pair(1, 2, 0.9)]
    assert cluster_pairs(pairs) == [{1, 2}]


def test_transitive_chain_merges_into_one_cluster():
    pairs = [pair(1, 2, 0.9), pair(3, 4, 0.85), pair(2, 3, 0.8)]
    assert cluster_pairs(pairs) == [{1, 2, 3, 4}]


def test_star_topology_forms_one_cluster():
    pairs = [pair(1, 2, 0.9), pair(1, 3, 0.85), pair(1, 4, 0.8)]
    assert cluster_pairs(pairs) == [{1, 2, 3, 4}]


# --- sort_cluster ---


def test_two_unit_cluster_returns_units_in_natural_order():
    pairs = [pair(1, 2, 0.9)]
    assert sort_cluster({1, 2}, pairs) == [1, 2]


def test_nearest_neighbor_path_order():
    # 2-3: 0.95 (best pair), 3-1: 0.8, 2-1: 0.5
    # starts [2, 3], then 1 is closer to 3 (0.8) than to 2 (0.5) → [2, 3, 1]
    pairs = [pair(2, 3, 0.95), pair(3, 1, 0.8), pair(2, 1, 0.5)]
    assert sort_cluster({1, 2, 3}, pairs) == [2, 3, 1]


def test_four_unit_chain_follows_nearest_neighbor():
    pairs = [
        pair(1, 3, 0.95),
        pair(3, 2, 0.85),
        pair(2, 4, 0.75),
        pair(1, 2, 0.4),
        pair(1, 4, 0.3),
        pair(3, 4, 0.35),
    ]
    assert sort_cluster({1, 2, 3, 4}, pairs) == [1, 3, 2, 4]


def test_single_unit_returns_single_unit():
    assert sort_cluster({42}, []) == [42]


# --- build_clusters ---


def test_build_clusters_groups_transitive_pairs():
    pairs = [pair(1, 2, 0.9), pair(2, 3, 0.8), pair(4, 5, 0.7)]
    assert build_clusters(pairs) == [
        Cluster(unit_ids=[1, 2, 3], min_similarity=0.8, max_similarity=0.9),
        Cluster(unit_ids=[4, 5], min_similarity=0.7, max_similarity=0.7),
    ]


def test_build_clusters_min_max_similarity():
    pairs = [pair(1, 2, 0.9), pair(2, 3, 0.7), pair(1, 3, 0.8)]
    assert build_clusters(pairs) == [
        Cluster(unit_ids=[1, 2, 3], min_similarity=0.7, max_similarity=0.9),
    ]


def test_build_clusters_sorted_by_average_similarity_descending():
    pairs = [pair(1, 2, 0.95), pair(3, 4, 0.6)]
    assert build_clusters(pairs) == [
        Cluster(unit_ids=[1, 2], min_similarity=0.95, max_similarity=0.95),
        Cluster(unit_ids=[3, 4], min_similarity=0.6, max_similarity=0.6),
    ]


def test_build_clusters_highest_similarity_pair_leads_cluster():
    pairs = [pair(1, 2, 0.95), pair(2, 3, 0.7), pair(1, 3, 0.6)]
    assert build_clusters(pairs) == [
        Cluster(unit_ids=[1, 2, 3], min_similarity=0.6, max_similarity=0.95),
    ]


# --- reorder_clusters ---


def test_reorder_clusters_rebuilds_min_max_from_reranked_pairs():
    clusters = [Cluster(unit_ids=[1, 2], min_similarity=0.9, max_similarity=0.9)]
    reranked = [pair(1, 2, 0.97)]
    assert reorder_clusters(clusters, reranked) == [
        Cluster(unit_ids=[1, 2], min_similarity=0.97, max_similarity=0.97),
    ]


def test_reorder_clusters_sorts_by_max_descending():
    clusters = [
        Cluster(unit_ids=[1, 2], min_similarity=0.9, max_similarity=0.9),
        Cluster(unit_ids=[3, 4], min_similarity=0.8, max_similarity=0.8),
    ]
    # second cluster gets a bigger boost
    reranked = [pair(1, 2, 0.91), pair(3, 4, 0.98)]
    result = reorder_clusters(clusters, reranked)
    assert [c.unit_ids for c in result] == [[3, 4], [1, 2]]


def test_reorder_clusters_reorders_units_within_cluster():
    # Original pairs would have ordered as [2, 3, 1]; with reranked scores
    # making 1-2 the strongest pair, ordering should change.
    clusters = [Cluster(unit_ids=[2, 3, 1], min_similarity=0.5, max_similarity=0.95)]
    reranked = [pair(1, 2, 0.99), pair(2, 3, 0.6), pair(1, 3, 0.7)]
    result = reorder_clusters(clusters, reranked)
    assert result[0].unit_ids == [1, 2, 3]


# --- filter_clusters ---


def test_filter_clusters_keeps_clusters_at_or_above_threshold():
    clusters = [
        Cluster(unit_ids=[1, 2], min_similarity=0.9, max_similarity=0.95),
        Cluster(unit_ids=[3, 4], min_similarity=0.8, max_similarity=0.92),
        Cluster(unit_ids=[5, 6], min_similarity=0.5, max_similarity=0.7),
    ]
    result = filter_clusters(clusters, threshold=0.93)
    assert [c.unit_ids for c in result] == [[1, 2]]


def test_filter_clusters_empty_when_all_below_threshold():
    clusters = [Cluster(unit_ids=[1, 2], min_similarity=0.5, max_similarity=0.6)]
    assert filter_clusters(clusters, threshold=0.93) == []
