from pathlib import Path

from slopo.result.identity import canonical_cluster_order
from slopo.result.models import AnalyzeResult


def format_analyze(result: AnalyzeResult, source_dir: Path) -> str:
    clusters, units = result
    clusters = canonical_cluster_order(clusters)
    blocks: list[str] = []
    for i, hc in enumerate(clusters, 1):
        lines = [f"cluster {i} ({hc.hash}):"]
        records = sorted(
            (units[uid] for uid in hc.cluster.unit_ids),
            key=lambda r: r.file_path,
        )
        for record in records:
            path = str(source_dir.resolve() / record.file_path)
            lines.append(f"    {path}:{record.start_line}-{record.end_line}")
        blocks.append("\n".join(lines) + "\n")
    return "\n".join(blocks)
