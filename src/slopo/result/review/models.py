from dataclasses import dataclass


@dataclass
class UnitRange:
    id: int
    start_line: int
    end_line: int


@dataclass
class LineRange:
    start: int  # 1-indexed, inclusive
    end: int  # 1-indexed, inclusive


@dataclass
class ChangedFile:
    path_db: str
    is_new: bool
    changed_ranges: list[LineRange]


@dataclass
class GitChange:
    path_git: str
    is_new: bool
    changed_ranges: list[LineRange]
