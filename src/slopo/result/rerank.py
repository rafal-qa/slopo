from pathlib import PurePosixPath

from slopo.result import boost
from slopo.result.models import Cluster, SimilarPair, UnitRecord


def path_hops(path_a: str, path_b: str) -> int:
    dir_a = PurePosixPath(path_a).parent.parts
    dir_b = PurePosixPath(path_b).parent.parts
    common = 0
    for x, y in zip(dir_a, dir_b):
        if x != y:
            break
        common += 1
    return (len(dir_a) - common) + (len(dir_b) - common)


def rerank_pair_score(
    pair: SimilarPair,
    unit_a: UnitRecord,
    unit_b: UnitRecord,
) -> float:
    if unit_a.file_path == unit_b.file_path:
        b = boost.same_file(_line_distance(unit_a, unit_b))
    else:
        b = boost.cross_dir(path_hops(unit_a.file_path, unit_b.file_path))
    return pair.similarity * (1 + b)


def rerank_cluster_pairs(
    pairs_in_cluster: list[SimilarPair],
    units: dict[int, UnitRecord],
) -> list[SimilarPair]:
    reranked: list[SimilarPair] = []
    for pair in pairs_in_cluster:
        unit_a = units[pair.unit_id_a]
        unit_b = units[pair.unit_id_b]
        new_score = rerank_pair_score(pair, unit_a, unit_b)
        reranked.append(
            SimilarPair(
                similarity=new_score,
                unit_id_a=pair.unit_id_a,
                unit_id_b=pair.unit_id_b,
            )
        )
    return reranked


def rerank_all_clusters(
    clusters: list[Cluster],
    pairs: list[SimilarPair],
    units: dict[int, UnitRecord],
) -> list[SimilarPair]:
    reranked: list[SimilarPair] = []
    for cluster in clusters:
        members = set(cluster.unit_ids)
        in_cluster = [
            p for p in pairs if p.unit_id_a in members and p.unit_id_b in members
        ]
        reranked.extend(rerank_cluster_pairs(in_cluster, units))
    return reranked


def _line_distance(a: UnitRecord, b: UnitRecord) -> int:
    if a.end_line < b.start_line:
        return b.start_line - a.end_line
    if b.end_line < a.start_line:
        return a.start_line - b.end_line
    return 0
