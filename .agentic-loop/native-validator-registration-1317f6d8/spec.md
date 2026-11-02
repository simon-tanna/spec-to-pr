# Native validator registration

## Context

The user accepted native spec-design-validator registration for Claude Code and Codex, with native preference and the existing bundled fallback. They confirmed an explicit setup command for the current project. The canonical rubric is skills/spec-design-validator/SKILL.md; scripts/build-distribution.py generates the existing Claude plugin role and bundled copies.

## Goals

1. Generate standalone Claude and Codex adapters from the canonical rubric and keep the existing Claude plugin adapter.
2. Ship explicit project setup from each independently installed validator-related skill: spec-design-validator, validating-specs, and agentic-loop.
3. Make each registration self-contained, with copied reference resources and no dependency on the source checkout, sibling skills, or CLAUDE_PLUGIN_ROOT.
4. Prefer native validators when exposed by the running host, retaining fresh generic workers with bundled roles otherwise.
5. Preserve unrelated files and locally modified registrations on repeated setup.
6. Document registration accurately without claiming improved finding quality without comparative evidence.

## Non-goals

Other native roles, automatic registration during validation, changes to reviewer criteria or output contracts, and changes to the parent's permissions, sandbox, MCP configuration, and model selection are outside this validator-specific work. Existing Claude plugin behavior remains supported.

## Architecture and components

### Canonical generation

Extend scripts/build-distribution.py to generate standalone host payloads and check their drift. Host wrappers provide metadata, worker instructions, and reference mapping; the reviewer rubric comes from the existing canonical skill. Keep the Claude plugin's plugin-specific reference mapping separate from standalone mapping.

### Explicit project setup

Ship a standard-library Python command in all three relevant skills:

```text
python3 <installed-skill>/scripts/setup-validator.py --host claude|codex|both [--project-root <directory>]
```

The host option is required; project root defaults to the current directory. Locate payloads relative to the script itself. Install .claude/agents/spec-design-validator.md and/or .codex/agents/spec-design-validator.toml. Copy reference resources and ownership metadata into a dedicated project-local spec-to-pr directory outside agent-discovery directories. Embed the selected project's absolute resource paths, with correct Markdown/TOML escaping.

Preflight all destinations before writes. Create missing files and accept identical files. Update managed files only when their contents match recorded ownership hashes. Conflicts or local modifications produce nonzero exit with conflicting paths and no planned writes. Preserve unrelated files. Rerunning after a project move refreshes managed absolute paths under the same protections. Ordinary I/O failure need not promise transactional rollback, but must report failure accurately and leave a recoverable state.

Report created, updated, and unchanged registrations, plus new-session/reload guidance. File installation does not prove runtime discovery. Setup only targets the selected project; no user-wide registration or permission changes.

### Host adapters

Standalone Claude retains the existing applicable tool exclusions and worker instructions, replacing CLAUDE_PLUGIN_ROOT with project resources. Retain the existing Claude model behavior rather than introducing model changes.

Codex uses supported TOML fields name, description, and developer_instructions. Omit optional model overrides and unsupported parent-policy overrides. Its read-only requirement is an instruction subject to inherited permissions, not an independent sandbox.

### Dispatch

Update canonical skills/validating-specs/references/dispatch.md and rebuild its copies. Prefer an available registered validator only when the exposed host spawn schema supports selecting it. Registration-file presence is insufficient; this session's Codex spawn tool has no agent-type selector. Retain fresh context and generic bundled-role fallback when native selection is unavailable. Preserve explicit generic worker selections and errors for unavailable external custom roles.

A native worker that starts and fails follows the existing review failure policy; do not silently bypass that failure with generic fallback. Continue supplying task-specific artifact paths, required tooling, lens, and output instructions regardless of role selection.

### Documentation

Document commands, destinations, conflicts, managed updates, rerunning after skill upgrades/project moves, host reload requirements, plugin versus standalone registration, and fallback behavior. Keep setup guidance out of the reviewer rubric's always-loaded instructions.

## Test strategy and acceptance criteria

- Generation tests prove host syntax, rubric parity, complete reference payloads, and drift detection (goals 1, 3).
- Temporary-project integration tests exercise both hosts and both together, repeat setup, managed updates, local changes/conflicts, unrelated files, spaces and escaping in paths, invalid arguments, and moved projects. Conflict preflight must preserve all planned destinations (goals 2, 3, 5).
- Installation closure tests/evaluator exercise setup from each relevant skill installed alone, in default and copy modes, after removing the source checkout (goals 2, 3).
- Dispatch contract tests cover native preference, schema-dependent availability, fresh bundled fallback, explicit generic selections, and existing failure policy (goal 4).
- Verify documented commands against CLI behavior and inspect claims for unsupported quality comparisons (goals 2, 6).
- Run the repository offline regression suite and distribution drift check. Record actual host discovery/spawn smoke results separately from file generation tests; unavailable runtime verification is incomplete evidence, not a passing runtime test.

## Resolved decisions

The user authorized native adapters, native preference with fallback, a single canonical rubric, and explicit project setup. Python, generated packaging locations, ownership hashes, conflict preflight, and command spelling are implementation choices by the planner. Preserving user content avoids expanding setup authority. Retain existing host model behavior and permissions; no new permission authority is requested.

## Open questions

None. The design is ready for human review before implementation.

## Risks

Host formats and discovery vary by version. Local Codex is 0.166.0 and its current exposed spawn tool cannot select native agents; keep fallback and report runtime evidence precisely. Existing custom registrations can collide; fail safely. Copied registrations can become stale after upgrades or moves; rerun setup. Absolute reference paths require correct escaping. Claude tool exclusions do not prevent arbitrary shell mutations, and Codex instructions do not provide a new sandbox; do not claim stronger isolation than the host provides.
