import numpy as np

from slopo.result.models import SimilarPair


def find_similar_pairs(
    embeddings: dict[int, np.ndarray],
    similarity_threshold: float,
    block_size: int,
) -> list[SimilarPair]:
    unit_ids = list(embeddings.keys())
    n = len(unit_ids)
    if n == 0:
        return []

    matrix = np.stack([embeddings[uid] for uid in unit_ids])
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)

    pairs: list[SimilarPair] = []
    for start in range(0, n, block_size):
        end = min(start + block_size, n)
        block = matrix[start:end] @ matrix.T
        rows, cols = np.where(block >= similarity_threshold)
        for r, c in zip(rows, cols):
            global_r = start + int(r)
            global_c = int(c)
            if global_r < global_c:
                pairs.append(
                    SimilarPair(
                        similarity=float(block[r, c]),
                        unit_id_a=unit_ids[global_r],
                        unit_id_b=unit_ids[global_c],
                    )
                )

    pairs.sort(key=lambda p: p.similarity, reverse=True)
    return pairs
