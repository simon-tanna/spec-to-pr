# Harness model selection

Codex: omit per-child model overrides. Use the configured inherited child default,
which may be affected by harness subagent defaults; do not promise that its model
always equals the parent. Record the effective model when observable. Never pass
Claude model aliases or mutate native configurations during the run.

The remaining tiering guidance applies only to Claude Code. Required review is
always a fresh child carrying the complete bundled role, even when native role
registration is absent. There is no controller-inline fallback for required work.

# Model Tiering

Subagent model resolves in this precedence: per-call `model:` argument on the Agent tool > agent definition frontmatter (`.claude/agents/<name>.md`) > parent's model (set by `--model` in the workflow's `claude_args`). The controller is pinned to Opus by the workflow; subagents follow their frontmatter unless this skill overrides per call.

Pass `model:` explicitly on every Agent dispatch listed below. Do not edit agent frontmatter to tune for this loop — other callers depend on those defaults. The roles below (planner, reviewer) are the configured agents (`agents.planner`, default `general-purpose`; `agents.reviewer`, default `code-reviewer`); the model assignment is keyed to the *role and its workload*, not to any specific agent. Per-call tiering applies to these fresh Claude child dispatches.

| Stage / call                          | Model               | Rationale                                                                                                 |
| ------------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------- |
| Stage 1 spec-planner (planner)        | opus                | one-shot synthesis: infer non-goals, draft test strategy, surface decision-forks                          |
| Stage 1 spec-reviewer (reviewer)      | sonnet              | structured 13-check audit; runs in a fix-and-re-review loop                                               |
| Stage 2 impl-planner Mode A (planner) | sonnet              | routing/dispatch JSON; constrained schema, bounded roster                                                 |
| Stage 2 specialist domain plans       | inherit frontmatter | scoped, well-bounded                                                                                      |
| Stage 2 impl-planner Mode B (planner) | opus                | one-shot cross-domain synthesis: merge + dedupe + sequence dependencies                                   |
| Stage 2 plan-reviewer (reviewer)      | sonnet              | structured TDD/granularity audit; runs in a fix-and-re-review loop                                        |
| Stage 3 task-implementer                | inherit frontmatter | mostly mechanical edits                                                                                   |
| Stage 3 spec-compliance review          | sonnet              | narrow per-commit check; runs N×M                                                                         |
| Stage 3 quality reviewer                | sonnet              | per-task review on small diffs; runs N×M — biggest cost amplifier. Final-review (opus) is the safety net. |
| Stage 4 final-review                    | opus                | one-shot full-branch diff, last gate before PR                                                            |
