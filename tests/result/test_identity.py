from slopo.result.identity import (
    canonical_cluster_order,
    cluster_hash,
    to_hashed_cluster,
)
from slopo.result.models import Cluster, HashedCluster, UnitRecord


def unit(unit_id: int, file_path: str, body_hash: str) -> UnitRecord:
    return UnitRecord(
        unit_id=unit_id,
        file_path=file_path,
        name="",
        start_line=1,
        end_line=10,
        body="",
        body_hash=body_hash,
    )


# --- cluster_hash ---


def test_same_units_in_different_order_produce_the_same_hash():
    units = {
        1: unit(1, "src/A.java", "h1"),
        2: unit(2, "src/B.java", "h2"),
    }
    a = cluster_hash(Cluster([1, 2], 0.9, 0.9), units)
    b = cluster_hash(Cluster([2, 1], 0.9, 0.9), units)
    assert a == b


def test_different_body_hash_produces_a_different_hash():
    units = {
        1: unit(1, "src/A.java", "h1"),
        2: unit(2, "src/A.java", "h2"),
    }
    a = cluster_hash(Cluster([1], 0.9, 0.9), units)
    b = cluster_hash(Cluster([2], 0.9, 0.9), units)
    assert a != b


def test_different_file_path_produces_a_different_hash():
    units = {
        1: unit(1, "src/A.java", "h1"),
        2: unit(2, "src/B.java", "h1"),
    }
    a = cluster_hash(Cluster([1], 0.9, 0.9), units)
    b = cluster_hash(Cluster([2], 0.9, 0.9), units)
    assert a != b


def test_hash_is_shortened_to_the_configured_length():
    units = {1: unit(1, "src/A.java", "h1")}
    assert len(cluster_hash(Cluster([1], 0.9, 0.9), units)) == 12


def test_produces_the_expected_hash_for_a_known_input():
    units = {
        1: unit(1, "src/A.java", "h1"),
        2: unit(2, "src/B.java", "h2"),
    }
    assert cluster_hash(Cluster([1, 2], 0.9, 0.9), units) == "9e1d4f8ca079"


# --- to_hashed_cluster ---


def test_pairs_each_cluster_with_its_hash_in_order():
    units = {
        1: unit(1, "a.java", "h1"),
        2: unit(2, "b.java", "h2"),
    }
    a = Cluster([1], 0.9, 0.9)
    b = Cluster([2], 0.8, 0.8)

    assert to_hashed_cluster([a, b], units) == [
        HashedCluster(a, cluster_hash(a, units)),
        HashedCluster(b, cluster_hash(b, units)),
    ]


# --- canonical_cluster_order ---


def test_clusters_sorted_by_max_similarity():
    a = HashedCluster(Cluster([1], 0.7, 0.7), "aaa")
    b = HashedCluster(Cluster([2], 0.5, 0.9), "bbb")
    c = HashedCluster(Cluster([3], 0.6, 0.8), "ccc")

    assert canonical_cluster_order([a, b, c]) == [b, c, a]


def test_equal_similarities_sorted_by_hash():
    a = HashedCluster(Cluster([1], 0.9, 0.9), "aaa")
    b = HashedCluster(Cluster([2], 0.9, 0.9), "mmm")
    c = HashedCluster(Cluster([3], 0.9, 0.9), "zzz")

    assert canonical_cluster_order([a, b, c]) == [c, b, a]


def test_ordering_ignores_similarity_differences_past_two_decimals():
    a = HashedCluster(Cluster([1], 0.90, 0.904), "aaa")
    b = HashedCluster(Cluster([2], 0.90, 0.902), "mmm")
    c = HashedCluster(Cluster([3], 0.90, 0.901), "zzz")

    assert canonical_cluster_order([a, b, c]) == [c, b, a]


def test_handles_empty_input():
    assert canonical_cluster_order([]) == []
