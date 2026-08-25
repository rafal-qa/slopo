import numpy as np
import pytest

from slopo.result.review.similarity import find_similar_pairs


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


def test_empty_embeddings_returns_empty():
    assert (
        find_similar_pairs(embeddings={}, changed_ids={10}, similarity_threshold=0.5)
        == []
    )


def test_no_changed_units_returns_empty():
    assert (
        find_similar_pairs(EMBEDDINGS, changed_ids=set(), similarity_threshold=0.5)
        == []
    )


def test_changed_units_not_in_embeddings_returns_empty():
    assert (
        find_similar_pairs(EMBEDDINGS, changed_ids={99}, similarity_threshold=0.5) == []
    )


def test_pairs_changed_unit_with_every_other_unit():
    pairs = find_similar_pairs(
        EMBEDDINGS, changed_ids={10}, similarity_threshold=NO_THRESHOLD
    )
    pair_ids = {(p.unit_id_a, p.unit_id_b) for p in pairs}
    assert pair_ids == {(10, 20), (10, 30), (10, 40)}


def test_computes_correct_cosine_similarity():
    pairs = find_similar_pairs(
        EMBEDDINGS, changed_ids={10, 20, 30}, similarity_threshold=NO_THRESHOLD
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
    pairs = find_similar_pairs(
        EMBEDDINGS, changed_ids={10, 20, 30}, similarity_threshold=0.5
    )
    assert {(p.unit_id_a, p.unit_id_b) for p in pairs} == {(10, 20), (30, 40)}


def test_sorts_by_similarity_descending():
    pairs = find_similar_pairs(
        EMBEDDINGS, changed_ids={10, 20, 30}, similarity_threshold=NO_THRESHOLD
    )
    similarities = [p.similarity for p in pairs]
    assert len(similarities) == 6
    assert similarities == sorted(similarities, reverse=True)


def test_normalizes_vectors_of_different_magnitudes():
    embeddings = {
        10: np.array([1.0, 0.0, 0.0], dtype=np.float32),
        20: np.array([5.0, 0.0, 0.0], dtype=np.float32),
    }
    pairs = find_similar_pairs(embeddings, changed_ids={10}, similarity_threshold=0.5)
    assert len(pairs) == 1
    assert pairs[0].similarity == pytest.approx(1.0)


def test_changed_unit_can_be_unit_id_a():
    embeddings = {10: V1, 20: V2}
    pairs = find_similar_pairs(
        embeddings, changed_ids={10}, similarity_threshold=NO_THRESHOLD
    )
    assert len(pairs) == 1
    assert pairs[0].unit_id_a == 10


def test_changed_unit_can_be_unit_id_b():
    embeddings = {10: V1, 20: V2}
    pairs = find_similar_pairs(
        embeddings, changed_ids={20}, similarity_threshold=NO_THRESHOLD
    )
    assert len(pairs) == 1
    assert pairs[0].unit_id_b == 20
