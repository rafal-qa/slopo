import numpy as np
import pytest

from slopo.result.analysis.similarity import find_similar_pairs


# v1..v4 chosen so two pairs are very similar (v1~v2, v3~v4),
# two pairs are orthogonal (v1-v3, v1-v4), and two pairs are weakly
# similar (v2-v3, v2-v4). Unit ids 10/20/30/40 are sparse to verify
# the function doesn't assume contiguous ids.
V1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
V2 = np.array([0.9, 0.1, 0.0], dtype=np.float32)
V3 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
V4 = np.array([0.0, 0.95, 0.05], dtype=np.float32)

COS_V1_V2 = 0.9938837
COS_V1_V3 = 0.0
COS_V1_V4 = 0.0
COS_V2_V3 = 0.1104315
COS_V2_V4 = 0.1102788
COS_V3_V4 = 0.9986178

EMBEDDINGS = {10: V1, 20: V2, 30: V3, 40: V4}

NO_THRESHOLD = -1.0
BLOCK = 1000


def test_empty_input_returns_no_pairs():
    assert find_similar_pairs({}, similarity_threshold=0.5, block_size=BLOCK) == []


def test_single_unit_returns_no_pairs():
    assert (
        find_similar_pairs({10: V1}, similarity_threshold=0.0, block_size=BLOCK) == []
    )


def test_normalizes_vectors_of_different_magnitudes():
    # Same direction, different magnitudes — cosine similarity must be 1.0.
    embeddings = {
        10: np.array([1.0, 0.0, 0.0], dtype=np.float32),
        20: np.array([5.0, 0.0, 0.0], dtype=np.float32),
    }
    pairs = find_similar_pairs(embeddings, similarity_threshold=0.5, block_size=BLOCK)
    assert len(pairs) == 1
    assert pairs[0].similarity == pytest.approx(1.0)


def test_orthogonal_vectors_filtered_by_positive_threshold():
    embeddings = {
        10: np.array([1.0, 0.0, 0.0], dtype=np.float32),
        20: np.array([0.0, 1.0, 0.0], dtype=np.float32),
    }
    assert (
        find_similar_pairs(embeddings, similarity_threshold=0.01, block_size=BLOCK)
        == []
    )


@pytest.mark.parametrize("block_size", [1, 2, 3, BLOCK])
def test_computes_correct_cosine_similarity(block_size: int):
    pairs = find_similar_pairs(
        EMBEDDINGS, similarity_threshold=NO_THRESHOLD, block_size=block_size
    )
    by_ids = {(p.unit_id_a, p.unit_id_b): p.similarity for p in pairs}

    assert len(pairs) == 6
    assert by_ids[(10, 20)] == pytest.approx(COS_V1_V2)
    assert by_ids[(10, 30)] == pytest.approx(COS_V1_V3)
    assert by_ids[(10, 40)] == pytest.approx(COS_V1_V4)
    assert by_ids[(20, 30)] == pytest.approx(COS_V2_V3)
    assert by_ids[(20, 40)] == pytest.approx(COS_V2_V4)
    assert by_ids[(30, 40)] == pytest.approx(COS_V3_V4)


def test_filters_pairs_below_threshold():
    pairs = find_similar_pairs(EMBEDDINGS, similarity_threshold=0.5, block_size=BLOCK)
    assert {(p.unit_id_a, p.unit_id_b) for p in pairs} == {(10, 20), (30, 40)}


def test_sorts_pairs_by_similarity_descending():
    pairs = find_similar_pairs(
        EMBEDDINGS, similarity_threshold=NO_THRESHOLD, block_size=BLOCK
    )
    similarities = [p.similarity for p in pairs]
    assert similarities == sorted(similarities, reverse=True)


def test_pair_ids_are_ordered_ascending():
    pairs = find_similar_pairs(
        EMBEDDINGS, similarity_threshold=NO_THRESHOLD, block_size=BLOCK
    )
    for p in pairs:
        assert p.unit_id_a < p.unit_id_b


def test_does_not_pair_unit_with_itself():
    embeddings = {10: V1, 20: V1.copy()}
    pairs = find_similar_pairs(embeddings, similarity_threshold=0.5, block_size=BLOCK)
    assert len(pairs) == 1
    assert (pairs[0].unit_id_a, pairs[0].unit_id_b) == (10, 20)
    assert pairs[0].similarity == pytest.approx(1.0)
