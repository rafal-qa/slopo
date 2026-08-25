from slopo.result.identity import canonical_cluster_order, cluster_hash
from slopo.result.models import Cluster, UnitRecord


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
    units = {1: unit(1, "src/A.java", "h1"), 2: unit(2, "src/B.java", "h2")}
    a = cluster_hash(Cluster([1, 2], 0.9, 0.9), units)
    b = cluster_hash(Cluster([2, 1], 0.9, 0.9), units)
    assert a == b


def test_different_body_hash_produces_a_different_hash():
    units = {1: unit(1, "src/A.java", "h1"), 2: unit(2, "src/A.java", "h2")}
    a = cluster_hash(Cluster([1], 0.9, 0.9), units)
    b = cluster_hash(Cluster([2], 0.9, 0.9), units)
    assert a != b


def test_different_file_path_produces_a_different_hash():
    units = {1: unit(1, "src/A.java", "h1"), 2: unit(2, "src/B.java", "h1")}
    a = cluster_hash(Cluster([1], 0.9, 0.9), units)
    b = cluster_hash(Cluster([2], 0.9, 0.9), units)
    assert a != b


def test_hash_is_shortened_to_the_configured_length():
    units = {1: unit(1, "src/A.java", "h1")}
    assert len(cluster_hash(Cluster([1], 0.9, 0.9), units)) == 12


# --- canonical_cluster_order ---


def test_clusters_sorted_by_max_similarity():
    units = {
        1: unit(1, "a.java", "h1"),
        2: unit(2, "b.java", "h2"),
        3: unit(3, "c.java", "h3"),
    }
    a = Cluster([1], 0.7, 0.7)
    b = Cluster([2], 0.5, 0.9)
    c = Cluster([3], 0.6, 0.8)

    assert canonical_cluster_order(clusters=[a, b, c], units=units) == [b, c, a]


def test_equal_similarities_sorted_by_hash(monkeypatch):
    hashes = {1: "aaa", 2: "mmm", 3: "zzz"}
    monkeypatch.setattr(
        "slopo.result.identity.cluster_hash",
        lambda c, _u: hashes[c.unit_ids[0]],
    )

    a = Cluster([1], 0.9, 0.9)
    b = Cluster([2], 0.9, 0.9)
    c = Cluster([3], 0.9, 0.9)

    assert canonical_cluster_order(clusters=[a, b, c], units={}) == [c, b, a]


def test_ordering_ignores_similarity_differences_past_two_decimals(monkeypatch):
    hashes = {1: "aaa", 2: "mmm", 3: "zzz"}
    monkeypatch.setattr(
        "slopo.result.identity.cluster_hash",
        lambda c, _u: hashes[c.unit_ids[0]],
    )

    a = Cluster([1], 0.90, 0.904)
    b = Cluster([2], 0.90, 0.902)
    c = Cluster([3], 0.90, 0.901)

    assert canonical_cluster_order(clusters=[a, b, c], units={}) == [c, b, a]


def test_handles_empty_input():
    assert canonical_cluster_order(clusters=[], units={}) == []
