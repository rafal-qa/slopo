import pytest

from slopo.result.analysis.selection import ClusterNotFoundError, select_cluster
from slopo.result.models import AnalyzeResult, Cluster, HashedCluster, UnitRecord


def _analysis() -> AnalyzeResult:
    units = {
        1: UnitRecord(1, "src/low.py", "low", 20, 30, "", "h1"),
        2: UnitRecord(2, "src/high.py", "high", 1, 10, "", "h2"),
    }
    low = HashedCluster(Cluster([1], 0.80, 0.85), "low-hash")
    high = HashedCluster(Cluster([2], 0.95, 0.99), "high-hash")
    return AnalyzeResult(clusters=[low, high], units=units)


def test_selects_top_ranked_cluster_when_hash_is_none():
    selected = select_cluster(_analysis(), None)

    assert [hc.hash for hc in selected.clusters] == ["high-hash"]


def test_selects_named_cluster_by_hash():
    selected = select_cluster(_analysis(), "low-hash")

    assert [hc.hash for hc in selected.clusters] == ["low-hash"]


def test_raises_for_unknown_hash():
    with pytest.raises(ClusterNotFoundError):
        select_cluster(_analysis(), "unknown")


def test_raises_with_requested_hash_when_there_are_no_results():
    with pytest.raises(ClusterNotFoundError) as exc_info:
        select_cluster(None, "wanted-hash")

    assert exc_info.value.cluster_hash == "wanted-hash"


def test_raises_without_hash_when_there_are_no_results():
    with pytest.raises(ClusterNotFoundError) as exc_info:
        select_cluster(None, None)

    assert exc_info.value.cluster_hash is None
