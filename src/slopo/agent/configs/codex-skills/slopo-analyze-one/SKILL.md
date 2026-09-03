---
name: slopo-analyze-one
description: Slopo reports an unreviewed similar code cluster, and agent reviews it.
license: AGPL-3.0-or-later
---

# Initialization

1. Read input added to skill invocation. It can be empty (not set), or it can contain a short hash.
2. Execute one command depending on input:
- If empty: `slopo agent-analyze --config-version=1 --single`
- If a hash was set, add it to command: `slopo agent-analyze --config-version=1 --single --cluster=<hash>`
- If the input doesn't look like a short hash, report this issue and stop.
3. Verify that the command succeeds (exit code 0). If it fails, report the error message and stop.

# Report structure

- The command should return a similar code report containing one cluster with file paths and line ranges.
- The first line contains the path to the ignore file.
- The cluster has a header line with a hash in format: `cluster 1 (hash):`

**Ignore file**
If the cluster should be ignored, its hash is inserted into the ignore file. One hash per line. Inline comments are allowed, e.g., `78a8d42e60e8 # your short note`

# Instructions

The report contains similar code. Take a quick look without deeper analysis and judge whether this is a duplication with a potential to take action on. If the code is only similar by coincidence or not an actionable duplicate:
- State this fact immediately without further analysis.
- Offer the user the option to add this cluster to the ignore file or discuss this further.
- Stop your job and wait for the user decision.

Otherwise, or when unsure, continue with deeper analysis to confirm.

Deeper analysis guidelines:
- Recall this project's standards and conventions related to code duplication and base your judgment on them (if any).
- State risks and trade-offs. Not every duplication or violation is worth solving, and the user is the one deciding.
- Judge a full refactor vs. minimal safe improvement. The user decides about the scope of change.
- Be aware that some duplication is done by design, or it's deliberate technical debt.
- Take into an account existing (or missing) tests - how well they protect and whether they need to be changed during refactor.
- Take into an account project context and broader impact, not only local change.

Include information allowing user to locate code, e.g. file paths, function/class names, but no line numbers.

## Handling user's decisions

After your deeper analysis, the user has a few options to continue.

The user may prefer to discuss this further before deciding. Offer this as one of the options.

If the user decides to ignore this duplication:
- Add cluster hash to the ignore file.

If the user decides to note this for later:
- Recall this project's standards and conventions related to handling tickets, notes, TODOs, etc.
- Assist the user to note somewhere a summary of analysis, and information allowing to locate affected code in the future. Cluster hash is not sufficient. Before writing a note, confirm where it should be written.
- Add cluster hash to the ignore file.

If the user decides to refactor now:
- Follow project conventions and the user's preferences related to implementing changes.