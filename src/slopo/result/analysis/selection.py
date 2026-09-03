from slopo.result.identity import canonical_cluster_order
from slopo.result.models import AnalyzeResult


class ClusterNotFoundError(Exception):
    def __init__(self, cluster_hash_value: str | None) -> None:
        self.cluster_hash = cluster_hash_value


def select_cluster(
    result: AnalyzeResult | None, cluster_hash_value: str | None
) -> AnalyzeResult:
    if result is None:
        raise ClusterNotFoundError(cluster_hash_value)

    clusters, units = result
    ordered = canonical_cluster_order(clusters)

    if cluster_hash_value is None:
        return AnalyzeResult(ordered[:1], units)

    for hc in ordered:
        if hc.hash == cluster_hash_value:
            return AnalyzeResult([hc], units)

    raise ClusterNotFoundError(cluster_hash_value)
