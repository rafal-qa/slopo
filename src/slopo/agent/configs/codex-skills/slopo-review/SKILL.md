---
name: slopo-review
description: Slopo reports similar code in Git changes, and agent reviews them.
license: AGPL-3.0-or-later
---

# Initialization

1. Read input added to skill invocation. It can be empty (not set), or it can contain Git base.
2. Execute one command depending on input:
- If empty: `slopo agent-review --config-version=1`
- If a base was set, add it to command: `slopo agent-review --config-version=1 --base=<base>`
- If the input doesn't look like a Git base, report this issue and stop.
3. Verify that the command succeeds (exit code 0). If it fails, report the error message and stop.

# Report structure

The command should return a similar code report containing either:
- List of clusters with file paths and line ranges.
- Message "No duplicates found".

Similar code was detected using embedding models, so many results are likely just similar by coincidence.
Lines marked with `*` are the user's changes. Unmarked lines are pre-existing similar code.
Line ranges point to similar code.

# Instructions

Judge whether the `*`-marked code introduces real duplication. The duplication may be between the changes and existing code, or between the changes themselves.

Recall this project's standards and conventions related to code duplication.

## Investigation is internal. Only the summary is external.

You may read surrounding code, callers to judge whether a similarity matters. Do it if the outcome needs it. The response says what the problem is, not what you saw to figure it out. Everything else is for follow-up if the user asks.

## First-turn output rules

For this response, you are not acting as a coding assistant giving analysis. You are a note-taker for the user's own review. The user will read the source themselves. Your job is to say what's worth their attention, not to explain what the code does or how it works.

For similarity that isn't real duplication, summarize briefly in high-level way.

For each similarity that matters:
- Include information allowing user to locate code, e.g. file paths, function/class names, but no line numbers.
- Name only the most important thing that is duplicated, in a one simple and short paragraph, as a high-level generalization without internals.
- Name the real problem it creates, in a one simple and short paragraph. Do not make up a problem to justify your choice. Do not propose solution, do not describe final shape.
- If project's standards or conventions related to code duplication are violated, name them. Otherwise, don't mention it.

Do NOT, in the first turn:
- describe how the code works: no variable names, no library calls, no algorithm steps, no walk-through
- sketch, name, or hint at a refactor, shared helper, or unification
- edit files

Group findings by how the code is actually related (same feature, same file, same underlying problem). Do not reference clusters or their numbers in your response.

## Follow-up analysis

User may ask for more information, deeper analysis, ask follow-up question, ask for advice or opinion.
In such a case, follow guidelines:
- State risks and trade-offs. Not every duplication or violation is worth solving, and the user is the one deciding.
- Judge a full refactor vs. minimal safe improvement. The user decides about the scope of change.
- Be aware that some duplication is done by design, or it's deliberate technical debt.
- Take into an account existing (or missing) tests - how well they protect and whether they need to be changed during refactor.
- Take into an account project context and broader impact, not only local change.