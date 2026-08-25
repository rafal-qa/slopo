from slopo.result.models import SimilarPair, UnitRecord


def exclude_overlapping_pairs(
    pairs: list[SimilarPair], units: dict[int, UnitRecord]
) -> list[SimilarPair]:
    # A unit nested in another unit's body (a local function, a callback, an
    # anonymous-class method) is indexed both on its own and inside its parent,
    # so the two overlap in source and score as near-identical. That similarity
    # is an artifact of the containment, not real duplication, so drop the pair.
    return [p for p in pairs if not _overlaps(units[p.unit_id_a], units[p.unit_id_b])]


def _overlaps(a: UnitRecord, b: UnitRecord) -> bool:
    if a.file_path != b.file_path:
        return False
    return _contains(a, b) or _contains(b, a)


def _contains(outer: UnitRecord, inner: UnitRecord) -> bool:
    return outer.start_line <= inner.start_line and inner.end_line <= outer.end_line
