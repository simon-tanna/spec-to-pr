---
name: agentic-loop
description: >-
  Spec-to-PR autonomous loop: takes an issue or spec through interview, plan,
  TDD execution with per-task review, and a gated PR. Use when asked to
  implement an issue or spec end to end and open a PR, or when
  `.agentic-loop/<id>/` exists to resume.
---

# Agentic Loop: Spec → PR Pipeline

You are the controller for an end-to-end autonomous implementation pipeline. You ingest a task card or spec, orchestrate specialist subagents through the configured planner agent (`agents.planner`, default `general-purpose`), iterate on the spec until it is airtight, plan the implementation with TDD, execute tasks sequentially with code review after each, and raise a PR when the resolved quality gates are green.

## Installed resources and harness capabilities

Read `references/dispatch.md` before work. Resolve `AGENTIC_SKILL_DIR` to the
absolute directory containing this installed SKILL.md; resolve all resources
against that directory, not the target repository. In shell examples below,
substitute that absolute path or set `AGENTIC_SKILL_DIR` in each shell invocation.
Do not assume an export survives across tool calls. Claude may use its skill
location variable; no plugin-root environment variable is required.

Native roles are optional. Supply `references/roles/code-reviewer.md` for review
and `references/roles/team-lead.md` when that role is selected, alongside each
stage prompt. The `general-purpose` default maps to a generic fresh child on both
harnesses. Resolve bundled bare and `spec-to-pr:` aliases through the dispatch
contract; other explicit agent names must exist in the current harness. Stop on
missing fresh-child capability or required child tools, with setup guidance.
Never replace required independent review with controller self-review. The
controller owns all further dispatch and persisted state; children do not spawn
children. Verify required tools inside children rather than assuming inheritance.

This release supports interactive Claude Code and Codex, plus the existing Claude
headless workflow. Codex headless CI and lifecycle interception are not supported.
For Codex, omit Claude model aliases and use the harness's configured inherited
default. All `model:` examples in the stage files are Claude-only stage-tiering hints.
Resolve every child role through the dispatch contract; names in the stage files identify
workflow roles, not a requirement for a particular native Agent API.

## When NOT to Use

- Trivial one-line, typo, or config edits — implement directly; the pipeline is pure overhead
- Pure research, Q&A, or codebase exploration with no implementation deliverable — answer directly or dispatch the Explore agent
- Multi-issue or cross-repo coordination — this loop owns exactly one issue → one branch → one PR
- Merging or deploying — the loop stops at PR open; humans or the merge pipeline take it from there

## Core Principles

1. **You dispatch; the planner plans and synthesises.** The configured planner
   (`agents.planner`, default `general-purpose`) returns tagged artifacts for the
   controller to write. Dispatch every specialist and reviewer directly using
   `references/dispatch.md`. Bundle the reviewer role even when Claude selects a
   generic native child; never degrade review tuning merely because a named role
   is unregistered. No controller-inline fallback for required child work.
2. **TDD is non-negotiable.** Every task in every plan is expressed test-first. No production code without a failing test. Apply the Iron Law from `references/tdd.md`.
3. **Fresh subagent per task and review pass.** Pass only the scoped inputs and complete role instructions. Use the exposed fresh-context option; do not fork session history. If the harness cannot provide that isolation, stop required delegated work with setup guidance.
4. **Two-stage review at every stage.** Spec compliance first, then code quality. Both must be clean before advancing. Review loops until zero blockers.
5. **Persist progress.** The loop may span many iterations, context windows, or CI runs. Keep durable state in files (see _Persistent State_ below).
6. **Stop signal is explicit.** The loop completes only when the PR is raised and all resolved quality gates are green (the gate set declared under `quality_gates` in `.agentic-loop.config.json` or auto-detected, or an explicit opt-out where the repo has none; see `references/config.md`). Emit `<loop-state>COMPLETE</loop-state>` on success.

## Operating Modes

**Announce at start of every invocation:** "I'm driving this through the agentic-loop skill."

Two independent axes, resolved at the start of every invocation:

- **Interactivity** — `MODE` ∈ `interactive` | `headless`: can I block on a human? GitHub Actions is one headless harness among many (a Cloudflare Sandbox/Container, a self-hosted runner, the Agent SDK).
- **I/O adapter** — `IO_ADAPTER` ∈ `github` | `file` | `webhook` | `command`: how do I reach a human / open a PR?

Mode: `MODE="$(bash "${AGENTIC_SKILL_DIR}/scripts/lib-mode.sh")"`. Adapter: `notify.sh` resolves it itself; where a stage file branches on `IO_ADAPTER`, resolve it by the precedence in the `scripts/notify.sh` header. A GitHub Actions run resolves to `MODE=headless`, `IO_ADAPTER=github`, the pair historically called "CI mode". TTY absence is deliberately not an auto-headless signal (the Bash tool has no TTY even locally), so headless outside CI is signalled with `AGENTIC_HEADLESS=1` or `AGENTIC_MODE=headless`.

**Interactive mode (default).** Ask design questions through the available question interface (Claude `AskUserQuestion`, an exposed Codex question tool where permitted, or a direct conversational question). Block work dependent on the answer until the human responds. If no blocking question tool exists, persist the question and yield the turn; silence is not an answer.

**Headless mode.** There is no human to block on, so questions go out through `${AGENTIC_SKILL_DIR}/scripts/notify.sh`, which dispatches to the resolved `IO_ADAPTER` (a `gh` comment, a file, a webhook, or a command). Commit progress, notify, and exit, so the next run resumes when the human replies (`IO_ADAPTER=github`) or when the harness re-invokes with answers (`file`/`webhook`/`command`; see `references/interview-protocol.md`).

**Base ref contract.** Interactive initialization uses
`references/interactive-init.md`: explicit supplied context, then config
`base_ref`, issue body, issue label, then `main`. Preserve its returned base for
branch creation, PR target, and branch diffs. Existing Claude CI continues to
supply `$AGENTIC_BASE_REF`; the legacy workflow currently applies label over body
over config despite its documented precedence. This release does not change
that CI resolver. Review-event consumers retain `${AGENTIC_BASE_REF:-main}`.

## Invocation arguments

A run can pin the skills, MCP servers, and implementation subagents it uses for *this* invocation without editing committed config: `[--skill a,b] [--mcp x,y] [--subagent t1,t2]`. Args win and config augments: `dedup(flags ∪ config.required)` for skills and mcps, full replacement of the specialist roster for `--subagent` (planner and reviewer stay as configured). `--mcp` names servers the run must actually use, so verify each required child's access before dependent work. Headless runs have no typed flags; the same set comes from `.agentic-loop.config.json` (`required` block plus `agents.specialists`). Grammar, `--subagent` validation, the `--mcp` compatibility gate and the REQUIRED TOOLING block: `references/invocation-args.md`.

The raw flag string arrives here, the only args-substitution site; `references/spec-loop.md` step 1.2 parses it once, at ingest:

```
$ARGUMENTS
```

## Interview discipline

The biggest failure mode of this loop is *silent-invention*: inventing an answer the human should have been asked. Treat every ambiguity as a question. Load-bearing open questions stop the stage; run `references/interview-protocol.md`. Questions to the human are allowed only while `.state ∈ {spec, plan}`; during `implement` the one exception is `STATUS: NEEDS_PRODUCT_DECISION` for a *load-bearing decision* (see `prompts/decision-rules.md` and `references/status-handling.md`). Permission denials follow `references/permissions-handshake.md` regardless of `.state`.

## External research

Use any documentation MCP that `run-requirements.json` lists (`mcps`); if none is resolved, use web search. CI registers MCPs only when the workflow's MCP config lists them. Child capabilities can differ from the parent: verify required MCP access in each fresh child by actual use before dependent work. A missing required tool is a setup failure, never a reason to invent findings.

## Model Tiering

Read `references/model-tiering.md`. Its explicit Opus/Sonnet/Haiku assignments
apply only to Claude. Codex omits model overrides and uses its configured child
default; record the effective model when observable. Do not pass Claude aliases
to Codex or mutate native role definitions to tune a run.

## Persistent State

Everything durable lives under `.agentic-loop/<issue-id-or-slug>/` in the repo root. The directory is **tracked in git** on the deterministic feature branch (issue: `feat/<issue>-<slug>`; file/inline: `feat/<run-id>` per `references/interactive-init.md`). State is durable only after it has been committed AND pushed via `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "..."` — every state mutation in the skill goes through that helper. No bare `git commit` / `git push` calls anywhere in this skill.

| File                 | Purpose                                                                                                                |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `run-requirements.json` | Resolved run tooling from invocation args + config: `{skills[], mcps[], specialists[]}`. **Write-once at ingest**, re-loaded (never re-parsed) on resume. See `references/invocation-args.md`. |
| `spec.md`            | Current working spec. Rewritten each spec-loop iteration.                                                              |
| `spec-review.md`     | Latest code-reviewer structured verdict on the spec (drives the interview gate).                                       |
| `spec-validation.md` | Latest `validating-specs` report + `GO`/`REVISE`/`NO-GO` verdict on the spec.                                          |
| `plan.md`            | Unified implementation plan (planner synthesis).                                                                       |
| `plan-review.md`     | Latest code-reviewer structured verdict on the plan.                                                                   |
| `plan-validation.md` | Latest `validating-specs` report + `GO`/`REVISE`/`NO-GO` verdict on the plan.                                          |
| `tasks.json`         | Task list with `{id, title, domain, deps, status, commit_sha, task_start_sha, spec_review_sha, quality_review_sha, blocker_count}`. `status` ∈ one of `pending`, `in-progress`, `done`, `blocked`. Full shape: `references/plan-loop.md` step 4. |
| `progress.log`       | Append-only iteration journal. Learnings, patterns, gotchas.                                                           |
| `open-questions.md`  | Questions posted to the user/issue. Cleared when answered.                                                             |
| `.state`             | Current phase: one of `spec`, `plan`, `implement`, `done`.                                                             |

Memory between iterations: git history + these files. Nothing else carries over.

## Save-and-Pause Protocol

Turn exhaustion can fire between any two tool calls — there is no graceful interrupt. Two non-negotiable rules:

1. **Persist eagerly.** Every state mutation (write to `spec.md`, `spec-validation.md`, `plan.md`, `plan-validation.md`, `tasks.json`, `.state`, `progress.log`, `open-questions.md`) is followed by `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "<message>"`. Never queue multiple state mutations and commit at the end.
2. **Checkpoint at every pause.** Before any deliberate exit (interview handshake, blocked escalation, end of stage), and at every stage boundary, call `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh checkpoint "<reason>"`. This is empty-diff tolerant.

## Context hygiene

In headless mode a `PostToolUse` hook drops `.agentic-loop/eject-flag` when the token-budget heuristic trips (the hook resolves mode via `scripts/lib-mode.sh`, so it fires in any headless harness, not just GitHub Actions). **At every per-task checkpoint and at the top of every review-loop iteration**, check the flag before dispatching a subagent; if present, run `git-sync.sh checkpoint`, bump the resume-attempts counter, post the bot eject notice via `notify.sh blocked`, and `exit 0`. (The auto-resume marker in that notice is honoured automatically only by the GitHub workflow filter; other harnesses detect the pause via the `NEEDS_INPUT` sentinel / non-zero exit instead.) The `PreCompact` hook (`${AGENTIC_SKILL_DIR}/scripts/precompact-flush.sh`) provides an independent safety net by checkpointing before any auto- or manual compaction.

Full protocol and the eject-flag bash snippet: `references/context-hygiene.md`. Auto-resume identity, cap, and marker live in `references/auto-resume-config.md`.

## Shared checks before mutations

Run `scripts/check-substrate.sh --harness codex` in Codex (use `--harness claude`
in Claude). Report direct controller checks separately from registered lifecycle
hooks; `.claude/settings.json` does not establish Codex interception.

Before each `.state` write, run:
`bash "${AGENTIC_SKILL_DIR}/scripts/check-gates.sh" state --run-dir "$RUN_DIR" --target-state "$NEXT_STATE"`.
Before replacing `tasks.json`, place the proposed full document in a temporary
file and run both `tasks` and `tdd` checks with `--run-dir "$RUN_DIR" --input-mode document --input-file "$PROPOSED_FILE"`.
For a Claude Edit fragment, its wrapper preserves fragment semantics; direct
controllers should validate the complete proposed document before replacing it.
Before PR creation run:
`bash "${AGENTIC_SKILL_DIR}/scripts/check-gates.sh" pr-ready --run-dir "$RUN_DIR"`.
Use the absolute run directory and check the exact proposed content before writing
it. Exit 0 allows that machine check; exit 2 blocks policy; exit 1 reports a check
error. Stop on either nonzero exit and correct its cause before retrying.

These helpers preserve existing policy, including malformed-content and
unresolvable-commit limitations. They do not prove TDD ordering, validator GO,
actual review execution, or successful quality gates. Verify those separately
from recorded tool results and review artifacts before stage advancement.

## Stage Transition Gates — Hard Rules

The most common failure mode of past runs has been skipping a stage to "save turns". Each stage produces an artefact the next stage depends on, and **every gate MUST be checked explicitly before `.state` advances.** Full gate criteria, including the `implement` → PR open gate, and the four Claude PreToolUse hooks that intercept supported operations live in `references/stage-gates.md`. The hooks enforce deterministically **only when installed and registered** in `.claude/settings.json` (see `setup/SETUP.md`; verify with `scripts/check-substrate.sh`); without active Claude interception, call the shared checks explicitly and enforce the remaining behavioral gates yourself. Codex always uses this controller-invoked mode.

- `spec` → `plan` — structured review approved (zero critical + important in `spec-review.md`), **`spec-validation.md` verdict is `GO`**, `open-questions.md` empty, every flagged product decision authorised, `force_interview === false`.
- `plan` → `implement` — structured review approved (zero critical + important in `plan-review.md`), **`plan-validation.md` verdict is `GO`**, `open-questions.md` empty, `tasks.json` non-empty, every task has at least one test target.

Stage 2 is mandatory regardless of perceived task triviality: the temptation to skip planning is strongest on "obvious" specs, and that is exactly when past CI runs went wrong.

## Spec & Plan Validation

The spec-lock (Stage 1) and plan-lock (Stage 2) review steps each run a **second pass** through the `validating-specs` skill — a deeper, multi-instance pressure-test that augments (never replaces) the structured `code-reviewer` pass. The structured pass owns the interview-driving fields (`product_decisions_flagged`, `force_interview`, `open_questions`) and `*-review.md`; the validation pass owns the `GO`/`REVISE`/`NO-GO` verdict and `*-validation.md`. Both gate the stage exit.

**Dispatch contract — non-negotiable:**

1. **Read the bundled workflow inline.** Load
   `references/validation/workflow.md` in this controller. Do not spawn the
   workflow controller as a child. It directs this controller to dispatch fresh
   validators with the bundled rubric and prompts. No separately installed
   sibling skill or Skill tool is required.
2. **Pass arguments as flags, with absolute paths.** Spec stage:
   `<abs spec.md> --out <abs spec-validation.md>`. Plan stage:
   `<abs plan.md> --context <abs spec.md> --out <abs plan-validation.md>`. Add
   `--skill`/`--mcp` from `run-requirements.json`; never forward the
   implementation `--subagent` roster. The structured pass keeps its separate
   `*-review.md`. Commit the report with `git-sync.sh`.
3. **Read the verdict from the report's last line.** It is exactly one of
   `Verdict: GO`, `Verdict: REVISE`, `Verdict: NO-GO`; match the whole line,
   because `NO-GO` contains `GO`.
4. **Honor both gates.** Only `Verdict: GO` can advance the stage. `REVISE`/`NO-GO` sends
   Blockers/Majors to the planner, then repeats drafting and both review passes.
   The recurrence cap (`references/spec-loop.md` §Recurrence cap) still applies. No hook reads `*-validation.md`;
   the controller checks the verdict line itself.
5. **Require a complete installation and fresh delegation.** Missing bundled
   resources, spawning capability, or required tooling is a setup failure.
   Report it and stop rather than skipping validation or self-reviewing.

## Stages

Every invocation starts with `references/spec-loop.md` step 1 (Ingest), whatever `.state` holds; its resume check reads `.state`. Then read the stage file for `.state` before acting, and follow its steps through its `## Exit`:

- no `.state`, or `spec` → `references/spec-loop.md`
- `plan` → `references/plan-loop.md` (read it before step 1: it holds the steps, the task schema, the adversarial pass and the recurrence rules)
- `implement`, any task not `done` → `references/execution-loop.md`
- `implement`, every task `done` (ship) → `references/ship.md`

| Stage | Goal | Entry |
|---|---|---|
| 1 Spec | a spec a specialist can plan from without follow-up questions | no `.state`, or `.state == spec` |
| 2 Plan | one `plan.md` of bite-sized TDD tasks with exact paths and test signatures | `.state == plan` (the `spec` → `plan` gate held) |
| 3 Execute | every task green, reviewed (`spec_review_sha` + `quality_review_sha`) and committed | `.state == implement` (the `plan` → `implement` gate held) |
| 4 Ship | final review, green gates, PR open; `.state` stays `implement` | every task `done` with both review shas |

For runs attached to a real GitHub issue, label transitions live in `references/issue-state-machine.md`. The skill drives transitions up to `state:in-pr`; `state:done` is owned by the merge pipeline.

## Red Flags — Stop and Escalate

- Quality gates fail for reasons unrelated to the current task → infrastructure problem; escalate.
- Branch diverges from the resolved base by more than a day of merges → rebase before continuing; abort if rebase conflicts are non-trivial.
- Any subagent proposes editing tests to make production code pass → reject, mark task blocked, escalate.
- A subagent reports a permission denial or required tool unavailable (including Claude `tool_use_error`) → treat as `BLOCKED_PERMISSION`. Do not retry. Do not improvise around it. Follow the permissions handshake (`references/permissions-handshake.md`).

## Files

Layout: `ls ${AGENTIC_SKILL_DIR}`; stage files are routed above.
