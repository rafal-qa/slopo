from pathlib import Path

from slopo.result.models import Cluster, HashedCluster, ReviewResult, UnitRecord
from slopo.result.review.text import format_review


def test_formats_single_cluster_with_changed_and_unchanged_units(tmp_path: Path):
    units = {
        1: UnitRecord(1, "src/a.py", "a", 1, 5, "", ""),
        2: UnitRecord(2, "src/b.py", "b", 10, 20, "", ""),
        3: UnitRecord(3, "src/c.py", "c", 30, 40, "", ""),
    }
    clusters = [HashedCluster(Cluster([1, 2, 3], 0.9, 0.95), "cluster-1-hash")]

    output = format_review(
        ReviewResult(clusters=clusters, units=units, changed_ids={2, 3}),
        tmp_path,
    )
    resolved = tmp_path.resolve()

    assert output == (
        f"cluster 1:\n"
        f"  * {resolved / 'src/b.py'}:10-20\n"
        f"  * {resolved / 'src/c.py'}:30-40\n"
        f"    {resolved / 'src/a.py'}:1-5\n"
    )


def test_orders_and_numbers_clusters_in_canonical_order_separated_by_blank_line(
    tmp_path: Path,
):
    units = {
        1: UnitRecord(1, "src/low.py", "low", 20, 30, "", ""),
        2: UnitRecord(2, "src/high.py", "high", 1, 10, "", ""),
    }
    low = HashedCluster(Cluster([1], 0.80, 0.85), "low-hash")
    high = HashedCluster(Cluster([2], 0.95, 0.99), "high-hash")

    output = format_review(
        ReviewResult(clusters=[low, high], units=units, changed_ids=set()),
        tmp_path,
    )
    resolved = tmp_path.resolve()

    assert output == (
        f"cluster 1:\n"
        f"    {resolved / 'src/high.py'}:1-10\n"
        f"\n"
        f"cluster 2:\n"
        f"    {resolved / 'src/low.py'}:20-30\n"
    )
