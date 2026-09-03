---
name: slopo-analyze-ignore
description: Slopo reports similar code in the whole codebase, and agent ignores non-duplicates.
license: AGPL-3.0-or-later
---

# Initialization

1. Execute command: `slopo agent-analyze --config-version=1`
2. Verify that the command succeeds (exit code 0). If it fails, report the error message and stop.

# Report structure

The command should return a similar code report containing either:
- List of clusters with file paths and line ranges.
- Message "No duplicates found".

If there are duplicates to analyze:
- The first line contains the path to the ignore file.
- Each cluster has a header line with number and hash in format: `cluster N (hash):`

Similar code was detected using embedding models, so many results are likely similar by coincidence.

# Instructions

Your task is to take a quick look at each cluster and mark as ignored the ones containing code that is not a duplication worth taking action on. An ignored cluster contains duplication obviously not worth taking action on, or it's similar by coincidence. If justifying to keep or ignore takes more than a short phrase, it is not obvious.

For every ignored cluster, insert its hash to the ignore file. One hash per line. Inline comments are allowed, e.g., `78a8d42e60e8 # your short note`

This work is a quick check, not deep analysis. Decide each cluster from a single look. The report size should not change how you judge one cluster. A report with a few tens of clusters is not a reason to dig deeper. A report with a few hundred is not a reason to rush.

Rules:
- Load only line ranges of code specified in the report. Do not read surrounding code or callers.
- Ignore only obvious false positives, when a quick check is enough to decide. When unsure, keep the cluster.
- If only part of the cluster is worth keeping, keep the whole cluster.

Process clusters in batches; don't load everything at once.