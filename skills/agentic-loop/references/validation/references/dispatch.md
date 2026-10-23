# Portable worker dispatch

The skill runs in the main controller session. Only that controller dispatches,
waits, synthesizes, asks the user questions, and changes workflow state. Workers
return artifacts/findings and never delegate further. Required validation and
review always use a fresh child; never replace them with the author's inline review.

## Resolve resources and roles

Resolve each resource path relative to the directory of the file that names it,
not the working repository or a plugin root. Give each child its role either as
a registered native role, or as the role file's absolute path with an instruction
to read it first; inline the role's content only when the child cannot read
files. Include the filled task template, exact artifact paths, and the working
repository path. Children inherit none of the skill's instructions,
conversation, MCP connections, or parent permissions.

`spec-design-validator` and `spec-to-pr:spec-design-validator` mean the bundled
validator role. (agentic-loop) `code-reviewer` and `spec-to-pr:code-reviewer`
mean the loop's bundled reviewer role; `team-lead` and `spec-to-pr:team-lead`
mean its bundled planning role. Only map roles present in the invoking skill's
resources. `general-purpose`, including explicit `--subagent general-purpose`
(agentic-loop), means a generic worker with the task prompt. A custom external
role must actually be available; report an unavailable-role error instead of
silently substituting it.

## Select the host adapter

Inspect the currently exposed spawn, wait, and result tool schemas. Tool names
and parameters below describe behavior, not a fixed API to invoke blindly.

- Claude Code plugin: use a registered native role when available. Otherwise
  use the available `general-purpose` Agent worker and inject the bundled role.
  Claude model tiers apply only through the Claude adapter.
- Standalone Claude skills: use the generic Agent worker with injected role;
  installing skills does not register native plugin agents or hooks.
- Codex: use its available child-agent tool and supported built-in worker role,
  with a fresh context (`fork_turns="none"` where supported). Omit model and
  reasoning overrides, inheriting the host's effective defaults. Do not require
  a `.codex/agents` installation or pretend Claude agent names are native types.

If a fresh child cannot be created, stop at the affected required gate and report
the missing capability. Do not claim a review occurred.

## Probe, dispatch, collect

The worker's first action is the probe: before any tool-dependent analysis it
runs one minimal read-only call per required tool (read the input file; fetch one
doc page) and reports call and result in its output. Parent tool discovery or a
worker's bare assertion is not evidence. A worker whose probe fails returns a
capability failure; the invoking skill decides retry or stop.

Pass the role as above, the task, input paths, success criteria, allowed scope,
required tools/skills, and output format. Review workers must not edit files;
this prompt restriction is not a filesystem sandbox. Use the host sandbox when
available. When inlining a validator role, resolve `{{REPORT_FORMAT}}` by
including the `report-format.md` beside the validator role.

Create a fresh worker for each lens and each review attempt, including after
revisions. Queue assignments when host capacity is exhausted; wait and collect
completed workers before dispatching the rest. Never skip a lens because slots
are full. Track assignment IDs, failures, and results. Collect every required
result before synthesis; the invoking skill decides retry or stop for a missing
or failed worker.

Return requests for product decisions to the controller. The controller uses the
host's supported question UI or ordinary conversation; (agentic-loop) it
preserves answers in the run artifacts and resumes from the recorded state. Do
not assume a Claude-only question tool exists or interpret elapsed time as
permission.
