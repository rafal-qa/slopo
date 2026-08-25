from slopo.result.models import UnitRecord
from slopo.result.report.markdown.shared import group_by_body_hash


def _unit(unit_id: int, body_hash: str, line: int = 1) -> UnitRecord:
    return UnitRecord(
        unit_id=unit_id,
        file_path=f"src/file{unit_id}.py",
        name=f"f{unit_id}",
        start_line=line,
        end_line=line + 1,
        body="body",
        body_hash=body_hash,
    )


def test_groups_units_sharing_a_body_hash():
    units = {
        1: _unit(1, "a"),
        2: _unit(2, "b"),
        3: _unit(3, "a"),
    }

    groups = group_by_body_hash([1, 2, 3], units)

    assert groups == [
        [units[1], units[3]],
        [units[2]],
    ]


def test_preserves_first_appearance_order_within_and_between_groups():
    units = {
        1: _unit(1, "a"),
        2: _unit(2, "a"),
        3: _unit(3, "b"),
    }

    groups = group_by_body_hash([2, 1, 3], units)

    assert groups == [
        [units[2], units[1]],
        [units[3]],
    ]


def test_collapses_exact_copies_into_one_group():
    units = {
        1: _unit(1, "a"),
        2: _unit(2, "a"),
    }

    groups = group_by_body_hash([1, 2], units)

    assert groups == [
        [units[1], units[2]],
    ]


def test_keeps_distinct_units_in_separate_groups():
    units = {
        1: _unit(1, "a"),
        2: _unit(2, "b"),
    }

    groups = group_by_body_hash([1, 2], units)

    assert groups == [
        [units[1]],
        [units[2]],
    ]
