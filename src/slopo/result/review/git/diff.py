import re

from slopo.result.review.models import LineRange, GitChange

# Hunk header: @@ -old_start,old_count +new_start,new_count @@
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_diff(diff_output: str) -> list[GitChange]:
    files: list[GitChange] = []
    for section in _split_file_sections(diff_output):
        result = _parse_file_section(section)
        if result is not None:
            files.append(result)
    return files


def parse_untracked(ls_output: str) -> list[GitChange]:
    files: list[GitChange] = []
    for line in ls_output.splitlines():
        path = line.strip()
        if path:
            files.append(GitChange(path_git=path, is_new=True, changed_ranges=[]))
    return files


def _split_file_sections(diff_output: str) -> list[str]:
    sections = re.split(r"^diff --git .+\n?", diff_output, flags=re.MULTILINE)
    return [s for s in sections if s]


def _parse_file_section(section: str) -> GitChange | None:
    path: str | None = None
    is_new = False
    is_deleted = False
    ranges: list[LineRange] = []

    for line in section.splitlines():
        if line.startswith("--- /dev/null"):
            is_new = True
        elif line.startswith("+++ /dev/null"):
            is_deleted = True
        elif line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("@@"):
            m = _HUNK_RE.match(line)
            if m:
                new_start = int(m.group(1))
                new_count = int(m.group(2)) if m.group(2) is not None else 1
                if new_count > 0:
                    end = new_start + new_count - 1
                else:
                    end = new_start  # deleted lines
                ranges.append(LineRange(start=new_start, end=end))

    if path is None or is_deleted:
        return None

    return GitChange(path_git=path, is_new=is_new, changed_ranges=ranges)
