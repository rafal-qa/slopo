import numpy as np

from slopo.result.models import SimilarPair


def find_similar_pairs(
    embeddings: dict[int, np.ndarray],
    changed_ids: set[int],
    similarity_threshold: float,
) -> list[SimilarPair]:
    unit_ids = list(embeddings.keys())
    n = len(unit_ids)
    if n == 0:
        return []

    # Positions in unit_ids list, for selecting rows from the numpy matrix.
    changed_indices = [i for i, uid in enumerate(unit_ids) if uid in changed_ids]
    if not changed_indices:
        return []

    matrix = np.stack([embeddings[uid] for uid in unit_ids])
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)

    sims = matrix[changed_indices] @ matrix.T
    rows, cols = np.where(sims >= similarity_threshold)

    pairs: list[SimilarPair] = []
    for r, c in zip(rows, cols):
        global_r = changed_indices[int(r)]
        global_c = int(c)
        pairs.append(
            SimilarPair(
                similarity=float(sims[r, c]),
                unit_id_a=unit_ids[global_r],
                unit_id_b=unit_ids[global_c],
            )
        )

    pairs = _deduplicate(pairs)
    pairs.sort(key=lambda p: p.similarity, reverse=True)
    return pairs


def _deduplicate(pairs: list[SimilarPair]) -> list[SimilarPair]:
    seen: set[tuple[int, int]] = set()
    result: list[SimilarPair] = []
    for p in pairs:
        key = (min(p.unit_id_a, p.unit_id_b), max(p.unit_id_a, p.unit_id_b))
        if key[0] != key[1] and key not in seen:
            seen.add(key)
            result.append(
                SimilarPair(similarity=p.similarity, unit_id_a=key[0], unit_id_b=key[1])
            )
    return result
