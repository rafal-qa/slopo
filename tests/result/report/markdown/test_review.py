from datetime import datetime

from slopo.result.models import Cluster, UnitRecord
from slopo.result.report.markdown.review import (
    build_cluster_review,
    build_index_review,
)

_UNITS = {
    1: UnitRecord(1, "src/A.java", "foo", 10, 20, "int foo() {}", "hashA"),
    2: UnitRecord(2, "src/B.java", "bar", 5, 15, "int bar() {}", "hashB"),
}
_CLUSTERS = [Cluster([1, 2], 0.95, 0.97)]
_GENERATED_AT = datetime(2026, 6, 19, 14, 30, 0)


def test_index_omits_hash_column():
    markdown = build_index_review(_CLUSTERS, _UNITS, _GENERATED_AT)

    assert (
        markdown
        == """\
Generated 2026-06-19 14:30:00

| Cluster                   | Score     | Code units | Unique files |
|---------------------------|-----------|------------|--------------|
| [Cluster 1](cluster-1.md) | 0.95-0.97 | 2          | 2            |
"""
    )


def test_index_counts_duplicates():
    units = {
        **_UNITS,
        3: UnitRecord(3, "src/C.java", "baz", 1, 11, "int foo() {}", "hashA"),
        4: UnitRecord(4, "src/A.java", "qux", 2, 12, "int foo() {}", "hashA"),
    }
    clusters = [Cluster([1, 2, 3, 4], 0.95, 0.97)]

    markdown = build_index_review(clusters, units, _GENERATED_AT)

    assert (
        markdown
        == """\
Generated 2026-06-19 14:30:00

| Cluster                   | Score     | Code units | Unique files |
|---------------------------|-----------|------------|--------------|
| [Cluster 1](cluster-1.md) | 0.95-0.97 | 4          | 3            |
"""
    )


def test_cluster_marks_changed_units():
    markdown = build_cluster_review(1, _CLUSTERS[0], _UNITS, changed_ids={1})

    assert (
        markdown
        == """\
## (1) score 0.95-0.97

---

- **CHANGED** `src/A.java` lines 10-20

```java
int foo() {}
```

---

- `src/B.java` lines 5-15

```java
int bar() {}
```
"""
    )
