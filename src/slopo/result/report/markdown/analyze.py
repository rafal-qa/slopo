from datetime import datetime

from slopo.result.models import HashedCluster, UnitRecord
from slopo.result.report.naming import cluster_filename
from slopo.result.report.markdown.shared import (
    format_table,
    group_by_body_hash,
    lang_tag,
    similarity_range,
)


def build_index_analyze(
    clusters: list[HashedCluster],
    units: dict[int, UnitRecord],
    generated_at: datetime,
) -> str:
    total = len(clusters)
    headers = ["Cluster", "Hash", "Score", "Code units", "Unique files"]
    rows: list[list[str]] = []
    for i, hc in enumerate(clusters, 1):
        link = f"[Cluster {i}]({cluster_filename(i, total)})"
        records = [units[uid] for uid in hc.cluster.unit_ids]
        unit_count = len(records)
        unique_files = len({record.file_path for record in records})
        rows.append(
            [
                link,
                hc.hash,
                similarity_range(hc.cluster),
                str(unit_count),
                str(unique_files),
            ]
        )
    timestamp = generated_at.strftime("%Y-%m-%d %H:%M:%S")
    return f"Generated {timestamp}\n\n{format_table(headers, rows)}"


def build_cluster_analyze(
    number: int,
    hashed: HashedCluster,
    units: dict[int, UnitRecord],
) -> str:
    lines: list[str] = [
        f"## ({number}) score {similarity_range(hashed.cluster)}\n",
        f"Hash: `{hashed.hash}`\n",
    ]
    for group in group_by_body_hash(hashed.cluster.unit_ids, units):
        lines.append("---\n")
        lang = lang_tag(group[0].file_path)
        for record in sorted(group, key=lambda r: r.file_path):
            lines.append(
                f"- `{record.file_path}` lines {record.start_line}-{record.end_line}"
            )
        lines.append(f"\n```{lang}\n{group[0].body}\n```\n")
    return "\n".join(lines)
