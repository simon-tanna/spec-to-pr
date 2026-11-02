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
repository path. Supply skill instructions and tool requirements explicitly. Use
fresh conversation context; inspect the child's actual permissions and tool
availability rather than assuming the parent's capabilities transfer.

`spec-design-validator` and `spec-to-pr:spec-design-validator` mean the bundled
validator role (the registered agent or `references/validator-role.md`), never
the standalone skill of that name. (agentic-loop) `code-reviewer` and `spec-to-pr:code-reviewer`
mean the loop's bundled reviewer role; `team-lead` and `spec-to-pr:team-lead`
mean its bundled planning role. Only map roles present in the invoking skill's
resources. `general-purpose` means a generic worker with the task prompt.
An explicit generic worker request stays generic for that worker.
In agentic-loop, explicit `--subagent general-purpose` selects the
implementation specialist roster only. This flag
does not change required validator or reviewer role selection.
A custom external role must actually be available; report an unavailable-role error
instead of silently substituting it.

## Select the host adapter

Inspect the currently exposed spawn, wait, and result tool schemas. Tool names
and parameters below describe behavior, not a fixed API to invoke blindly.

For the bundled validator on Claude Code or Codex, prefer the registered native
`spec-design-validator` when this session's exposed selector accepts that role.
This applies to plugin registrations and explicit project-local registrations.
File presence in `.claude/agents` or `.codex/agents` is insufficient: verify both
registration availability and a selectable agent-type parameter in the exposed
spawn schema. A Codex spawn schema without an agent-type selector uses a fresh
generic child with the bundled role, even when a definition exists on disk.

- Claude Code: select the available native role through Agent's supported role
  selector; otherwise inject the bundled role into a fresh generic child.
  Retain the existing Claude model tiers through the Claude adapter.
- Codex: select the available native role only through a supported agent-type
  selector; otherwise inject the bundled role into a supported generic child.
  Use fresh context (`fork_turns="none"` where supported). Omit model and
  reasoning overrides, inheriting the host's effective defaults.

Once a started native worker fails, apply the invoking workflow's existing
retry or stop policy. Never silently replace a failed native attempt with a
generic child. Every retry is fresh and retains the role, exact artifact paths,
required tooling, lens assignment, and output instructions. Setup is an explicit
user operation; dispatch never installs or repairs native registrations.

If a fresh child cannot be created, stop at the affected required gate and report
the missing capability. Do not claim a review occurred. `--single` still
dispatches one fresh child; loading the `spec-design-validator` skill inline in
this session is not a dispatch.

## Probe, dispatch, collect

The worker's first action is the probe: before any tool-dependent analysis it
runs one minimal read-only call per required tool (read the input file; fetch one
doc page) and reports call and result in its output. Parent tool discovery or a
worker's bare assertion is not evidence. A worker whose probe fails returns a
capability failure; the invoking skill decides retry or stop.

Pass the role as above, the task, input paths, success criteria, allowed scope,
required tools/skills, and output format. Review workers must not edit files;
this prompt restriction is not a filesystem sandbox. Use the host sandbox when
available.

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
