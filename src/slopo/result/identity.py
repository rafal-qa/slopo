import hashlib

from slopo.result.models import Cluster, UnitRecord

_HASH_LENGTH = 12


def canonical_cluster_order(
    clusters: list[Cluster], units: dict[int, UnitRecord]
) -> list[Cluster]:
    return sorted(
        clusters,
        key=lambda c: (round(c.max_similarity, 2), cluster_hash(c, units)),
        reverse=True,
    )


def cluster_hash(cluster: Cluster, units: dict[int, UnitRecord]) -> str:
    pairs = sorted(
        (units[uid].file_path, units[uid].body_hash) for uid in cluster.unit_ids
    )
    canonical = "\n".join(f"{path}\0{body_hash}" for path, body_hash in pairs)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:_HASH_LENGTH]
