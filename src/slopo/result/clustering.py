from slopo.result.models import Cluster, SimilarPair


def cluster_pairs(pairs: list[SimilarPair]) -> list[set[int]]:
    # Groups unit IDs into clusters by transitive similarity: if A~B and B~C,
    # all three end up in the same set. Each set in the result is one cluster.
    groups: list[set[int]] = []

    for pair in pairs:
        a, b = pair.unit_id_a, pair.unit_id_b
        matching = [g for g in groups if a in g or b in g]

        if not matching:
            groups.append({a, b})
        else:
            merged: set[int] = set()
            for g in matching:
                merged |= g
            merged |= {a, b}
            for g in matching:
                groups.remove(g)
            groups.append(merged)

    return groups


def sort_cluster(unit_ids: set[int], pairs: list[SimilarPair]) -> list[int]:
    # Orders units so adjacent pairs are as similar as possible. Starts with the
    # highest-similarity pair, then greedily appends the unit most similar to the
    # last one added. lookup is a symmetric dict {(a, b): similarity} for O(1) access.
    if len(unit_ids) <= 2:
        if len(unit_ids) == 2:
            a, b = sorted(unit_ids)
            return (
                [a, b]
                if _similarity(a, b, pairs) >= _similarity(b, a, pairs)
                else [b, a]
            )
        return list(unit_ids)

    lookup: dict[tuple[int, int], float] = {}
    for p in pairs:
        if p.unit_id_a in unit_ids and p.unit_id_b in unit_ids:
            lookup[(p.unit_id_a, p.unit_id_b)] = p.similarity
            lookup[(p.unit_id_b, p.unit_id_a)] = p.similarity

    def sim(a: int, b: int) -> float:
        return lookup.get((a, b), 0.0)

    sorted_ids = sorted(unit_ids)
    best_pair = max(
        ((a, b) for a in sorted_ids for b in sorted_ids if a != b),
        key=lambda ab: sim(ab[0], ab[1]),
    )

    path = [best_pair[0], best_pair[1]]
    remaining = unit_ids - {best_pair[0], best_pair[1]}

    while remaining:
        last = path[-1]
        next_unit = max(remaining, key=lambda u: sim(last, u))
        path.append(next_unit)
        remaining.remove(next_unit)

    return path


def reorder_clusters(
    clusters: list[Cluster], reranked_pairs: list[SimilarPair]
) -> list[Cluster]:
    result: list[Cluster] = []
    for cluster in clusters:
        members = set(cluster.unit_ids)
        in_cluster = [
            p
            for p in reranked_pairs
            if p.unit_id_a in members and p.unit_id_b in members
        ]
        ordered = sort_cluster(members, in_cluster)
        sims = [p.similarity for p in in_cluster]
        min_sim = min(sims)
        max_sim = max(sims)
        result.append(
            Cluster(unit_ids=ordered, min_similarity=min_sim, max_similarity=max_sim)
        )
    result.sort(key=lambda c: c.max_similarity, reverse=True)
    return result


def filter_clusters(clusters: list[Cluster], threshold: float) -> list[Cluster]:
    return [c for c in clusters if c.max_similarity >= threshold]


def build_clusters(pairs: list[SimilarPair]) -> list[Cluster]:
    raw_groups = cluster_pairs(pairs)
    clusters: list[Cluster] = []

    for group in raw_groups:
        ordered = sort_cluster(group, pairs)
        group_set = set(group)
        group_sims = [
            p.similarity
            for p in pairs
            if p.unit_id_a in group_set and p.unit_id_b in group_set
        ]
        min_sim = min(group_sims)
        max_sim = max(group_sims)
        clusters.append(
            Cluster(unit_ids=ordered, min_similarity=min_sim, max_similarity=max_sim)
        )

    clusters.sort(key=_avg_similarity, reverse=True)
    return clusters


def _avg_similarity(cluster: Cluster) -> float:
    return (cluster.min_similarity + cluster.max_similarity) / 2


def _similarity(a: int, b: int, pairs: list[SimilarPair]) -> float:
    for p in pairs:
        if (p.unit_id_a == a and p.unit_id_b == b) or (
            p.unit_id_a == b and p.unit_id_b == a
        ):
            return p.similarity
    return 0.0
