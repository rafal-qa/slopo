import re

CLUSTER_FILE_GLOB = "cluster-*.md"
CLUSTER_FILE_RE = re.compile(r"cluster-\d+\.md")


def cluster_filename(number: int, total: int) -> str:
    width = len(str(total))
    return f"cluster-{number:0{width}d}.md"
