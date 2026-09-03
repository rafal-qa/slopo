from pathlib import Path

from slopo.result.identity import canonical_cluster_order
from slopo.result.models import ReviewResult


def format_review(result: ReviewResult, source_dir: Path) -> str:
    clusters, units, changed_ids = result
    ordered = canonical_cluster_order(clusters)
    blocks: list[str] = []
    for i, hc in enumerate(ordered, 1):
        lines = [f"cluster {i}:"]
        records = sorted(
            (units[uid] for uid in hc.cluster.unit_ids),
            key=lambda r: (r.unit_id not in changed_ids, r.file_path),
        )
        for record in records:
            marker = "*" if record.unit_id in changed_ids else " "
            path = str(source_dir.resolve() / record.file_path)
            lines.append(f"  {marker} {path}:{record.start_line}-{record.end_line}")
        blocks.append("\n".join(lines) + "\n")
    return "\n".join(blocks)
