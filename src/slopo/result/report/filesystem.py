from datetime import datetime
from pathlib import Path

from slopo.result.identity import canonical_cluster_order
from slopo.result.models import HashedCluster, ReviewResult, UnitRecord
from slopo.result.report.markdown.analyze import (
    build_cluster_analyze,
    build_index_analyze,
)
from slopo.result.report.markdown.review import (
    build_cluster_review,
    build_index_review,
)
from slopo.result.report.naming import (
    CLUSTER_FILE_GLOB,
    CLUSTER_FILE_RE,
    cluster_filename,
)


def write_analyze_report(
    clusters: list[HashedCluster],
    units: dict[int, UnitRecord],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _clean_report_dir(output_dir)

    clusters = canonical_cluster_order(clusters)
    total = len(clusters)
    # newline="\n" prevents Windows text-mode from translating \n to \r\n. Code
    # unit bodies may already contain \r\n from CRLF source files; translation
    # would turn those into \r\r\n and render as extra blank lines.
    (output_dir / "index.md").write_text(
        build_index_analyze(clusters, units, datetime.now()),
        encoding="utf-8",
        newline="\n",
    )
    for i, hc in enumerate(clusters, 1):
        filename = cluster_filename(i, total)
        (output_dir / filename).write_text(
            build_cluster_analyze(i, hc, units),
            encoding="utf-8",
            newline="\n",
        )


def write_review_report(
    result: ReviewResult,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _clean_report_dir(output_dir)

    clusters, units, changed_ids = result
    ordered = [hc.cluster for hc in canonical_cluster_order(clusters)]
    total = len(ordered)
    (output_dir / "index.md").write_text(
        build_index_review(ordered, units, datetime.now()),
        encoding="utf-8",
        newline="\n",
    )
    for i, cluster in enumerate(ordered, 1):
        filename = cluster_filename(i, total)
        (output_dir / filename).write_text(
            build_cluster_review(i, cluster, units, changed_ids),
            encoding="utf-8",
            newline="\n",
        )


def _clean_report_dir(output_dir: Path) -> None:
    index = output_dir / "index.md"
    if index.is_file():
        index.unlink()
    for path in output_dir.glob(CLUSTER_FILE_GLOB):
        if CLUSTER_FILE_RE.fullmatch(path.name):
            path.unlink()
