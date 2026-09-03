from pathlib import Path

from slopo.result.analysis.text import format_analyze
from slopo.result.models import AnalyzeResult, Cluster, HashedCluster, UnitRecord


def test_formats_single_cluster_with_hash_header(tmp_path: Path):
    units = {
        1: UnitRecord(1, "src/a.py", "a", 1, 5, "", "h1"),
        2: UnitRecord(2, "src/b.py", "b", 10, 20, "", "h2"),
        3: UnitRecord(3, "src/c.py", "c", 30, 40, "", "h3"),
    }
    cluster = HashedCluster(Cluster([1, 2, 3], 0.9, 0.95), "abc123def456")

    output = format_analyze(
        AnalyzeResult(clusters=[cluster], units=units),
        tmp_path,
    )
    resolved = tmp_path.resolve()

    assert output == (
        f"cluster 1 (abc123def456):\n"
        f"    {resolved / 'src/a.py'}:1-5\n"
        f"    {resolved / 'src/b.py'}:10-20\n"
        f"    {resolved / 'src/c.py'}:30-40\n"
    )


def test_orders_and_numbers_clusters_in_canonical_order_separated_by_blank_line(
    tmp_path: Path,
):
    units = {
        1: UnitRecord(1, "src/low.py", "low", 20, 30, "", "h1"),
        2: UnitRecord(2, "src/high.py", "high", 1, 10, "", "h2"),
    }
    low = HashedCluster(Cluster([1], 0.80, 0.85), "low-hash")
    high = HashedCluster(Cluster([2], 0.95, 0.99), "high-hash")

    output = format_analyze(
        AnalyzeResult(clusters=[low, high], units=units),
        tmp_path,
    )
    resolved = tmp_path.resolve()

    assert output == (
        f"cluster 1 (high-hash):\n"
        f"    {resolved / 'src/high.py'}:1-10\n"
        f"\n"
        f"cluster 2 (low-hash):\n"
        f"    {resolved / 'src/low.py'}:20-30\n"
    )
