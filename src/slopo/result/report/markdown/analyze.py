from datetime import datetime

from slopo.result.identity import cluster_hash
from slopo.result.models import Cluster, UnitRecord
from slopo.result.report.naming import cluster_filename
from slopo.result.report.markdown.shared import (
    format_table,
    group_by_body_hash,
    lang_tag,
    similarity_range,
)


def build_index_analyze(
    clusters: list[Cluster],
    units: dict[int, UnitRecord],
    generated_at: datetime,
) -> str:
    total = len(clusters)
    headers = ["Cluster", "Hash", "Score", "Code units", "Unique files"]
    rows: list[list[str]] = []
    for i, cluster in enumerate(clusters, 1):
        link = f"[Cluster {i}]({cluster_filename(i, total)})"
        records = [units[uid] for uid in cluster.unit_ids]
        unit_count = len(records)
        unique_files = len({record.file_path for record in records})
        rows.append(
            [
                link,
                cluster_hash(cluster, units),
                similarity_range(cluster),
                str(unit_count),
                str(unique_files),
            ]
        )
    timestamp = generated_at.strftime("%Y-%m-%d %H:%M:%S")
    return f"Generated {timestamp}\n\n{format_table(headers, rows)}"


def build_cluster_analyze(
    number: int,
    cluster: Cluster,
    units: dict[int, UnitRecord],
) -> str:
    lines: list[str] = [
        f"## ({number}) score {similarity_range(cluster)}\n",
        f"Hash: `{cluster_hash(cluster, units)}`\n",
    ]
    for group in group_by_body_hash(cluster.unit_ids, units):
        lines.append("---\n")
        lang = lang_tag(group[0].file_path)
        for record in sorted(group, key=lambda r: r.file_path):
            lines.append(
                f"- `{record.file_path}` lines {record.start_line}-{record.end_line}"
            )
        lines.append(f"\n```{lang}\n{group[0].body}\n```\n")
    return "\n".join(lines)
