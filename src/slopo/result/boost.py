from math import log2


_CROSS_DIR_MAX_BOOST = 0.15
_CROSS_DIR_MAX_HOPS = 8

_SAME_FILE_MAX_BOOST = 0.1
_SAME_FILE_STEP_LINES = 250
_SAME_FILE_MAX_STEPS = 8


def cross_dir(hops: int) -> float:
    return _distance_boost(hops, _CROSS_DIR_MAX_HOPS, _CROSS_DIR_MAX_BOOST)


def same_file(line_distance: int) -> float:
    steps = line_distance // _SAME_FILE_STEP_LINES
    return _distance_boost(steps, _SAME_FILE_MAX_STEPS, _SAME_FILE_MAX_BOOST)


def _distance_boost(distance: int, max_distance: int, max_boost: float) -> float:
    capped = min(distance, max_distance)
    if capped <= 0:
        return 0.0
    return log2(1 + capped) / log2(1 + max_distance) * max_boost
