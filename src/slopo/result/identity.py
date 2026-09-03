import hashlib

from slopo.result.models import Cluster, HashedCluster, UnitRecord

_HASH_LENGTH = 12


def to_hashed_cluster(
    clusters: list[Cluster], units: dict[int, UnitRecord]
) -> list[HashedCluster]:
    return [
        HashedCluster(cluster, cluster_hash(cluster, units)) for cluster in clusters
    ]


def canonical_cluster_order(clusters: list[HashedCluster]) -> list[HashedCluster]:
    return sorted(
        clusters,
        key=lambda hc: (round(hc.cluster.max_similarity, 2), hc.hash),
        reverse=True,
    )


def cluster_hash(cluster: Cluster, units: dict[int, UnitRecord]) -> str:
    pairs = sorted(
        (units[uid].file_path, units[uid].body_hash) for uid in cluster.unit_ids
    )
    canonical = "\n".join(f"{path}\0{body_hash}" for path, body_hash in pairs)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:_HASH_LENGTH]
