import pytest

from slopo.result.boost import cross_dir, same_file


@pytest.mark.parametrize(
    "hops, expected",
    [
        (0, 0.0),
        (1, 0.047),
        (2, 0.075),
        (4, 0.11),
        (8, 0.15),
        (16, 0.15),
    ],
)
def test_cross_dir_boost(hops: int, expected: float):
    assert round(cross_dir(hops), 3) == expected


@pytest.mark.parametrize(
    "line_distance, expected",
    [
        (0, 0.0),
        (250, 0.032),
        (500, 0.05),
        (1000, 0.073),
        (2000, 0.1),
        (4000, 0.1),
    ],
)
def test_same_file_boost(line_distance: int, expected: float):
    assert round(same_file(line_distance), 3) == expected
