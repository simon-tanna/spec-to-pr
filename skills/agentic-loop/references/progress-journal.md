# Progress Journal

`progress.log` is append-only. It is the memory of the loop across iterations, context windows, and CI runs.

## Per-task Entry

Append after each task completes:

```
## <ISO timestamp> — <task-id> <task-title>
Commit: <short-sha>
Files: <comma-separated>
Notes:
- <what was built, one line>
- <anything surprising>
Learnings:
- <pattern discovered — only if reusable>
- <gotcha — only if non-obvious>
- <useful context — only if future tasks need it>
---
```

## Top-of-file Patterns Section

If a task revealed a **generally reusable** pattern, consolidate it into a `## Codebase Patterns` section at the top of the file (create it on first addition). One bullet per pattern. Examples:

```
## Codebase Patterns
- Integration tests: spin up the test database with the shared fixture helper, never hand-rolled setup
- Money math: store and compute in minor units (cents), round consistently, never use floats
- Public API handlers: validate input at the boundary with the shared schema, never trust the caller
- Workspace imports: import from the package alias, never deep relative paths across packages
```

Only add patterns that are project-wide. Story-specific detail stays in the per-task entry.

## What Not to Log

- Step-by-step narration of the work (the git log has that).
- Subagent thought process (noise).
- Temporary debugging detail.
- Anything that duplicates `CLAUDE.md` or `spec.md`.

## Size Cap

`progress.log` is loaded into context on resume, so unbounded growth becomes a context tax on long-running issues. Cap the **per-task entries** section at the 20 most recent entries:

- Before appending a new entry, count entries (each starts with `## <ISO timestamp> — `).
- If the count is ≥ 20, drop the oldest entry block (timestamp header through the trailing `---`).
- The `## Codebase Patterns` section at the top is preserved indefinitely — that is the durable memory.

The cap keeps the resume-context cost flat regardless of how many tasks the issue has churned through.

## CLAUDE.md Updates

If a pattern is broad enough to affect future unrelated work, also add it to the nearest `CLAUDE.md` in the affected directory. Examples:

- "When modifying the database package, run its migration test command before committing."
- "Background workers in this service write logs to stderr, never stdout."

Do this sparingly — CLAUDE.md is loaded into every conversation's context.
