from slopo.result.review.models import ChangedFile, UnitRange, LineRange, GitChange


def to_changed_file(
    git_changes: list[GitChange], source_dir_prefix: str
) -> list[ChangedFile]:
    result: list[ChangedFile] = []
    for gc in git_changes:
        if not source_dir_prefix:
            result.append(
                ChangedFile(
                    path_db=gc.path_git,
                    is_new=gc.is_new,
                    changed_ranges=gc.changed_ranges,
                )
            )
        elif gc.path_git.startswith(source_dir_prefix):
            result.append(
                ChangedFile(
                    path_db=gc.path_git[len(source_dir_prefix) :],
                    is_new=gc.is_new,
                    changed_ranges=gc.changed_ranges,
                )
            )
    return result


def match_changed_units(
    changed_files: list[ChangedFile],
    units_by_path: dict[str, list[UnitRange]],
) -> list[int]:
    matched_ids: list[int] = []

    for cf in changed_files:
        units = units_by_path.get(cf.path_db)
        if units is None:
            continue

        if cf.is_new:
            matched_ids.extend(u.id for u in units)
        else:
            for u in units:
                if _ranges_overlap(u.start_line, u.end_line, cf.changed_ranges):
                    matched_ids.append(u.id)

    return matched_ids


def _ranges_overlap(
    unit_start: int, unit_end: int, changed_ranges: list[LineRange]
) -> bool:
    return any(unit_start <= r.end and r.start <= unit_end for r in changed_ranges)
