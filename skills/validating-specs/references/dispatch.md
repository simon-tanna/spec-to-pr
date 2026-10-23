# Portable worker dispatch

The skill runs in the main controller session. Only that controller dispatches,
waits, synthesizes, asks the user questions, and changes workflow state. Workers
return artifacts/findings and never delegate further. Required validation and
review always use a fresh child; never replace them with the author's inline review.

## Resolve resources and roles

Resolve resource paths against this installed skill directory, not the working
repository or a plugin root. Read the role and task template and include their
actual content in the child prompt. Include exact artifact paths and the working
repository path. Do not assume children inherit skill instructions, conversation,
MCP connections, or parent permissions.

`spec-design-validator` and `spec-to-pr:spec-design-validator` mean the bundled
validator role; `code-reviewer` and `spec-to-pr:code-reviewer` mean the loop's
bundled reviewer role; `team-lead` and `spec-to-pr:team-lead` mean its bundled
planning role. Only map roles present in the invoking skill's resources.
`general-purpose`, including explicit `--subagent general-purpose`, means a
generic worker with the task prompt. A custom external role must actually be
available; report an unavailable-role error instead of silently substituting it.

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
the missing capability. Do not claim a review occurred. Optional copyediting
may be omitted only when it was not requested or made a required gate.

## Probe, dispatch, collect

Before a tool-dependent worker assignment, have a fresh child demonstrate the
required capability with a minimal read-only operation (for example reading the
input file, or fetching the requested library documentation). Record the actual
tool/result evidence. Parent tool discovery or a child's assertion of access is
not sufficient. If a required MCP tool/skill is absent in the child, report it
and stop dependent work; do not silently drop a requested augmentation.

Pass role content, the task, input paths, success criteria, allowed scope, required
tools/skills, and output format. Review workers must not edit files; this prompt
restriction is not a filesystem sandbox. Use the host sandbox when available.
Resolve `{{REPORT_FORMAT}}` in a validator role by including report-format.md.

Create a fresh worker for each lens and each review attempt, including after
revisions. Queue assignments when host capacity is exhausted; wait and collect
completed workers before dispatching the rest. Never skip a lens because slots
are full. Track assignment IDs, failures, and results. Collect every required
result before synthesis; a missing/failed worker cannot count as GO.

Return requests for product decisions to the controller. The controller uses the
host's supported question UI or ordinary conversation, preserves answers in the
run artifacts, and resumes from the recorded state. Do not assume a Claude-only
question tool exists or interpret elapsed time as permission.
