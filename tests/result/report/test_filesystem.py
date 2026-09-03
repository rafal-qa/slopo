from pathlib import Path

from slopo.result.models import Cluster, HashedCluster, ReviewResult, UnitRecord
from slopo.result.report.filesystem import write_analyze_report, write_review_report


_UNITS = {
    1: UnitRecord(1, "src/A.java", "foo", 10, 20, "int foo() {}", "hashA"),
    2: UnitRecord(2, "src/B.java", "bar", 5, 15, "int bar() {}", "hashB"),
}
_CLUSTERS = [HashedCluster(Cluster([1, 2], 0.95, 0.97), "cluster-1-hash")]


def test_creates_output_directory_including_missing_parents(tmp_path: Path):
    output_dir = tmp_path / "nested" / "slopo-report"

    write_analyze_report(_CLUSTERS, _UNITS, output_dir)

    assert (output_dir / "index.md").is_file()
    assert (output_dir / "cluster-1.md").is_file()


def test_writes_into_an_existing_directory(tmp_path: Path):
    output_dir = tmp_path / "report"
    output_dir.mkdir()

    write_analyze_report(_CLUSTERS, _UNITS, output_dir)

    assert (output_dir / "index.md").is_file()
    assert (output_dir / "cluster-1.md").is_file()


def test_leaves_files_not_owned_by_the_tool(tmp_path: Path):
    output_dir = tmp_path / "report"
    output_dir.mkdir()
    (output_dir / "README.md").write_text("keep me")
    (output_dir / "cluster-notes.md").write_text("keep me")
    (output_dir / "cluster-1.txt").write_text("keep me")

    write_analyze_report(_CLUSTERS, _UNITS, output_dir)

    assert (output_dir / "README.md").read_text() == "keep me"
    assert (output_dir / "cluster-notes.md").read_text() == "keep me"
    assert (output_dir / "cluster-1.txt").read_text() == "keep me"


def test_removes_stale_cluster_files_from_a_larger_previous_run(tmp_path: Path):
    output_dir = tmp_path / "report"

    many = [HashedCluster(Cluster([1, 2], 0.95, 0.97), "stale-hash") for _ in range(12)]
    write_analyze_report(many, _UNITS, output_dir)
    assert (output_dir / "cluster-01.md").is_file()
    assert (output_dir / "cluster-12.md").is_file()

    write_analyze_report(_CLUSTERS, _UNITS, output_dir)

    assert (output_dir / "cluster-1.md").is_file()
    assert not (output_dir / "cluster-01.md").exists()
    assert not (output_dir / "cluster-12.md").exists()


def test_writes_changed_marker_to_cluster_file(tmp_path: Path):
    output_dir = tmp_path / "report"

    write_review_report(ReviewResult(_CLUSTERS, _UNITS, {1}), output_dir)

    cluster = (output_dir / "cluster-1.md").read_text()
    assert "**CHANGED** `src/A.java`" in cluster
    assert "**CHANGED** `src/B.java`" not in cluster
    assert "`src/B.java`" in cluster
