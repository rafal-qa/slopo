from slopo.result.models import SimilarPair, UnitRecord
from slopo.result.overlap import exclude_overlapping_pairs


def _unit(unit_id: int, file_path: str, start: int, end: int) -> UnitRecord:
    return UnitRecord(
        unit_id=unit_id,
        file_path=file_path,
        name=f"unit{unit_id}",
        start_line=start,
        end_line=end,
        body="",
        body_hash="",
    )


def test_drops_pair_where_one_unit_is_nested_in_the_other():
    units = {
        1: _unit(1, "a.js", 1, 10),
        2: _unit(2, "a.js", 3, 6),
    }
    pairs = [SimilarPair(similarity=0.99, unit_id_a=1, unit_id_b=2)]
    assert exclude_overlapping_pairs(pairs, units) == []


def test_containment_detected_regardless_of_pair_order():
    units = {
        1: _unit(1, "a.js", 3, 6),
        2: _unit(2, "a.js", 1, 10),
    }
    pairs = [SimilarPair(similarity=0.99, unit_id_a=1, unit_id_b=2)]
    assert exclude_overlapping_pairs(pairs, units) == []


def test_keeps_pair_of_disjoint_units_in_same_file():
    units = {
        1: _unit(1, "a.js", 1, 5),
        2: _unit(2, "a.js", 7, 12),
    }
    pairs = [SimilarPair(similarity=0.99, unit_id_a=1, unit_id_b=2)]
    assert exclude_overlapping_pairs(pairs, units) == pairs


def test_keeps_pair_with_same_line_span_in_different_files():
    units = {
        1: _unit(1, "a.js", 1, 10),
        2: _unit(2, "b.js", 3, 6),
    }
    pairs = [SimilarPair(similarity=0.99, unit_id_a=1, unit_id_b=2)]
    assert exclude_overlapping_pairs(pairs, units) == pairs


def test_keeps_overlapping_units_that_do_not_contain_each_other():
    units = {
        1: _unit(1, "a.js", 1, 6),
        2: _unit(2, "a.js", 4, 10),
    }
    pairs = [SimilarPair(similarity=0.99, unit_id_a=1, unit_id_b=2)]
    assert exclude_overlapping_pairs(pairs, units) == pairs
