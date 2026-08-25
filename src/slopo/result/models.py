from typing import NamedTuple


class Cluster(NamedTuple):
    unit_ids: list[int]
    min_similarity: float
    max_similarity: float


class SimilarPair(NamedTuple):
    similarity: float
    unit_id_a: int
    unit_id_b: int


class UnitRecord(NamedTuple):
    unit_id: int
    file_path: str
    name: str
    start_line: int
    end_line: int
    body: str
    body_hash: str
