---
name: agentic-loop
description: >-
  Use for autonomous end-to-end implementation of a SINGLE spec, task card,
  GitHub issue, or feature description: ingest the requirement, then plan with
  TDD, run review loops and quality gates, and open one PR. Triggers on "run the
  agentic loop", "implement this issue", "take this from spec to PR",
  "build this out end to end", "implement this spec and open a PR", a GitHub Action invoking
  the agent with an issue payload — and on ANY hand-off of a spec/issue/feature
  for full implementation, even when the loop is not named. Prefer over
  plan-mode or brainstorming when a concrete spec/issue is handed off to build
  end-to-end: this skill plans AND implements AND ships. Do NOT use for trivial
  one-line/typo/config edits, pure research or Q&A with no code deliverable,
  multi-issue or cross-repo work, or merging/deploying.

# Main-session controller with harness-dependent dispatch, filesystem, shell,
# research, and question tools. No Claude-specific restricted tool list.
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
default. All `model:` examples below are Claude-only stage-tiering hints.
Resolve every child role through the dispatch contract; names below identify
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
6. **Stop signal is explicit.** The loop completes only when the PR is raised and all resolved quality gates are green (the gate set declared in `.agentic-loop.config.json` or auto-detected — or an explicit opt-out where the repo has none; see _Quality gates_). Emit `<loop-state>COMPLETE</loop-state>` on success.

## Operating Modes

**Announce at start of every invocation:** "I'm driving this through the agentic-loop skill."

### Interactive mode (default)

Triggered in an interactive Claude Code or Codex session. Ask design questions
through the available question interface (Claude `AskUserQuestion`, an exposed
Codex question tool where permitted, or a direct conversational question). Block
work dependent on the answer until the human responds. If no blocking question
tool exists, persist the question and yield the turn; silence is not an answer.

The interview fires on **every** §9 Open Question and every `product_decisions_flagged[]` entry where `authorised_by_source: false` — batched per stage in a single round. Do not wait for `force_interview: true` to start asking; non-empty §9 or any unauthorised flagged decision is itself sufficient. The local-session under-triggering pattern this rule fixes was the controller assuming its own confidence in an answer let it skip the prompt.

### Headless mode (`MODE=headless`)

Triggered when `MODE` resolves to `headless` (GitHub Actions, `$CI`, or an explicit `AGENTIC_HEADLESS=1` / `AGENTIC_MODE=headless` — see the resolver above). There is no human to block on, so questions are emitted through `${AGENTIC_SKILL_DIR}/scripts/notify.sh` (which dispatches to the resolved `IO_ADAPTER` — `gh` comment, a file, a webhook, or a command). Do not block on human answers during a single run; commit progress, notify, and exit so the next run resumes when the human replies (`IO_ADAPTER=github`) or when the harness re-invokes with answers (`file`/`webhook`/`command` — see `references/ci-mode.md §Interview Handshake`). GitHub Actions is the `MODE=headless, IO_ADAPTER=github` case and behaves exactly as before.

**Base ref contract.** Interactive initialization uses
`references/interactive-init.md`: explicit supplied context, then config
`base_ref`, issue body, issue label, then `main`. Preserve its returned base for
branch creation, PR target, and branch diffs. Existing Claude CI continues to
supply `$AGENTIC_BASE_REF`; the legacy workflow currently applies label over body
over config despite its documented precedence. This release does not change
that CI resolver. Review-event consumers retain `${AGENTIC_BASE_REF:-main}`.

## Invocation Arguments

A run can be steered with flags — pin the skills, MCP servers, and implementation subagents it uses for
*this* invocation without editing committed config:

```
[--skill a,b] [--mcp x,y] [--subagent t1,t2]
```

- **--skill** — project skills the run must consult (threaded into planner + specialist prompts, and
  forwarded to the `validating-specs` passes).
- **--mcp** — MCP servers the run must actually use. Verify each required
  child's access before dependent work; parent access and generic role names
  alone are insufficient. See the compatibility gate in `references/invocation-args.md`.
- **--subagent** — specialist roster override, fully replacing
  `agents.specialists`. Planner and reviewer are untouched. Resolve bundled
  aliases and generic defaults through `references/dispatch.md`; explicit
  external types must be available and code-capable.

Precedence: **args win, config/auto-detect augment** — `dedup(flags ∪ config.required)` for skills/mcps,
full roster replacement for `--subagent`. Parsing, resolution, validation, and persistence to
`run-requirements.json` all happen once at **Stage 1 Ingest** (the single args-substitution site); this
section is documentation. Full grammar, `--subagent` validation rules, the `--mcp` compatibility gate, and the
REQUIRED TOOLING block that dispatch prompts embed live in `references/invocation-args.md`.

In headless/CI there are no typed flags (the args placeholder is empty); the same `{skills, mcps, specialists}`
set is sourced from `.agentic-loop.config.json` (`required` block + `agents.specialists`).

## Interview Discipline — Ask, Do Not Guess

The single biggest failure mode of this loop is silently inventing an answer the human should have been asked — **silent-invention**. Treat every ambiguity as a question first, an assumption never. Both modes must interview — interactive via the available question interface, headless via `${AGENTIC_SKILL_DIR}/scripts/notify.sh questions` with the Open-Questions template.

**Headless is notify-and-exit, never decide-and-proceed.** In headless mode there is no human to block on — but that is a reason to *pause*, not a licence to *decide*. Once you surface an open question you MUST post it via `notify.sh`, commit, and **exit** (per `references/interview-protocol.md`); `.state` stays `spec`/`plan` and the run ends until answers arrive. You may NOT resolve a surfaced question by adopting a "conservative default", a "documented assumption", or a "safe" choice and continuing — recording an assumption and shipping IS the silent-invention failure this section exists to prevent, and "a human will confirm before merge" is not a substitute for the human answering *first*. This is strictest for load-bearing product decisions (data custody, access control, irreversible/destructive operations, retention/privacy, billing, security trust boundaries, breaking public contracts): the instant one is surfaced, the loop halts and exits — it never advances to `implement` or ships a PR under an unanswered load-bearing decision, no matter how conservative the default looks. The deterministic backstop is the state-transition gate hook, which refuses any `plan` or `implement` transition while `open-questions.md` is non-empty — and refuses `plan` unless `spec-review.md` records `verdict:"approved"` with `force_interview:false` (see `references/stage-gates.md`); when that hook is not registered, you enforce the same rule yourself.

**You MUST raise an interview when any of these are true** (Stage 1 or Stage 2 only):

- **Decision-fork trigger (primary rule).** The spec drafter or reviewer can name a second defensible option for any decision the spec resolves — across product, architectural, library, or threshold categories — and `source.md` does not literally authorise the chosen one. This is the bar defined in `prompts/spec-planner.md` §Step 0.5 and audited in `prompts/spec-reviewer.md` check 13. "I am confident in my answer" is not a reason to skip the question; the rule is about whether an alternative exists, not about your certainty.
- The source spec/issue leaves a product decision unmade (auth model, data shape, UX flow, error semantics, retention, threshold values).
- A non-goal is implied but not stated, and getting it wrong would mean rework.
- An acceptance criterion is missing for a stated goal.
- A dependency, contract, schema, or external API is referenced without a concrete version/path.
- The planner's spec draft surfaces an `Open Questions` section — every line there is a mandatory interview, never silently resolved.
- Any specialist returns "I assumed X because the spec did not say" — promote that assumption to a question.
- `source.md` matches any phrase in the spec-planner's Step 0 prose-context phrase list (see `prompts/spec-planner.md` for the current list, which includes the explicit "stop and ask" / "if unclear" cues plus softer self-flags like "tbd", "unsure", "either", "open question") or a line-anchored `Default:` line. If any match, the loop MUST surface ≥1 interview round before §9 can be empty. The spec-planner's §0 Interview Trace tracks this; an empty §9 with a non-empty §0 Interview Trace is a process violation.
- The spec-reviewer's `force_interview` field is `true`, or `product_decisions_flagged[]` contains any entry with `authorised_by_source: false` (any category — original product list, `architecture`, `library`, or `threshold`).

**One round, batched.** Collect every open question for the current stage, post them together, then pause. Do not drip-feed the human one question per turn — that wastes runs in CI and human attention everywhere.

**Never** enter Stage 3 (implement) with a non-empty `open-questions.md`. The plan-loop exit gate verifies this.

Detect mode at the start of every invocation. Two independent axes — do not conflate them:

- **Interactivity** — `MODE` ∈ `interactive` | `headless`: can I block on a human? GitHub Actions is one headless harness among many (a Cloudflare Sandbox/Container, a self-hosted runner, the Agent SDK).
- **I/O adapter** — `IO_ADAPTER` ∈ `github` | `file` | `webhook` | `command`: how do I reach a human / open a PR?

```bash
# Axis A — interactivity. Most explicit signal wins; defaults to interactive so
# local Claude Code sessions are unchanged. (scripts/lib-mode.sh is the single
# source of truth; the two context hooks resolve mode the same way.)
MODE="$(bash "${AGENTIC_SKILL_DIR}/scripts/lib-mode.sh")"

# Axis B — I/O adapter. Explicit env/config wins; else github when gh is usable
# (preserves today's GitHub Actions behaviour), else file (a gh-free sandbox).
IO_ADAPTER="${AGENTIC_IO_ADAPTER:-$(jq -r '.io.adapter // empty' .agentic-loop.config.json 2>/dev/null || true)}"
if [ -z "$IO_ADAPTER" ]; then
  { [ "${GITHUB_ACTIONS:-}" = "true" ] || gh auth status >/dev/null 2>&1; } \
    && IO_ADAPTER=github || IO_ADAPTER=file
fi
```

A GitHub Actions run resolves to `MODE=headless`, `IO_ADAPTER=github` — the pair historically called "CI mode"; its behaviour is unchanged. TTY-absence is deliberately NOT an auto-headless signal (the Bash tool has no TTY even locally), so headless outside CI must be signalled via `AGENTIC_HEADLESS=1` or `AGENTIC_MODE=headless`.

## External Research (context7)

When the controller or any dispatched specialist needs current library or framework docs, prefer context7 over training-data recall:

- **CI tool names**: `mcp__context7__resolve-library-id` then `mcp__context7__query-docs`. The workflow's "Write MCP config" step registers the `context7` server via `--mcp-config` and `claude_args` allow-lists both tools.
- **Local tool names** (plugin-namespaced): `mcp__plugin_context7_context7__resolve-library-id` then `mcp__plugin_context7_context7__query-docs`. Provided by the `plugin:context7` plugin.
- **Fallback**: if context7 returns nothing useful for the library (e.g. a niche or newly-released package it has not indexed yet), fall back to `WebFetch` on the library's docs domain.

Use the tool names actually exposed by the harness. The names above describe
Claude installations only. Child capabilities can differ from the parent: verify
required MCP access in each fresh child by actual use before dependent work.
A missing required tool is a setup failure, never a reason to invent findings.

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
| `tasks.json`         | Task list with `{id, title, deps, status, commit_sha}`. `status` ∈ one of `pending`, `in-progress`, `done`, `blocked`. |
| `progress.log`       | Append-only iteration journal. Learnings, patterns, gotchas.                                                           |
| `open-questions.md`  | Questions posted to the user/issue. Cleared when answered.                                                             |
| `.state`             | Current phase: one of `spec`, `plan`, `implement`, `done`.                                                             |

Memory between iterations: git history + these files. Nothing else carries over.

## Save-and-Pause Protocol

Turn exhaustion can fire between any two tool calls — there is no graceful interrupt. Two non-negotiable rules:

1. **Persist eagerly.** Every state mutation (write to `spec.md`, `spec-validation.md`, `plan.md`, `plan-validation.md`, `tasks.json`, `.state`, `progress.log`, `open-questions.md`) is followed by `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "<message>"`. Never queue multiple state mutations and commit at the end.
2. **Checkpoint at every pause.** Before any deliberate exit (interview handshake, blocked escalation, end of stage), and at every stage boundary, call `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh checkpoint "<reason>"`. This is empty-diff tolerant.

## Context Hygiene

In headless mode a `PostToolUse` hook drops `.agentic-loop/eject-flag` when the token-budget heuristic trips (the hook resolves mode via `scripts/lib-mode.sh`, so it fires in any headless harness, not just GitHub Actions). **At every per-task checkpoint and at the top of every review-loop iteration**, check the flag before dispatching a subagent; if present, run `git-sync.sh checkpoint`, bump the resume-attempts counter, post the bot eject notice via `notify.sh blocked`, and `exit 0`. (The auto-resume marker in that notice is honoured automatically only by the GitHub workflow filter; other harnesses detect the pause via the `NEEDS_INPUT` sentinel / non-zero exit instead.) The `PreCompact` hook (`${AGENTIC_SKILL_DIR}/scripts/precompact-flush.sh`) provides an independent safety net by checkpointing before any auto- or manual compaction.

Full protocol and the eject-flag bash snippet: `references/context-hygiene.md`. Auto-resume identity, cap, and marker live in `references/auto-resume-config.md`.

## Mid-Stage Question Protocol

Open-questions are allowed **only** while `.state ∈ {spec, plan}`. Once `.state == implement`, mark blockers in `tasks.json` and let `progress.log` / plan revision carry the gap forward — never ping the human mid-implementation. The single exception is `STATUS: NEEDS_PRODUCT_DECISION` for load-bearing product calls (data custody/ownership, access control, irreversible/destructive operations, billing/fees, data retention/privacy, security trust boundaries, external-service trust, breaking public-contract changes — plus any configured `risk_categories`); see `references/status-handling.md §NEEDS_PRODUCT_DECISION`.

Full protocol (Stage 1/2 append-and-pause flow, mechanical clearing of `open-questions.md`, Stage 3 no-interview rule): `references/interview-protocol.md`. Permission denials follow `references/permissions-handshake.md` regardless of `.state`.

## Loop Start / Resume Banner

At the very start of every headless invocation, post **exactly one** banner via `${AGENTIC_SKILL_DIR}/scripts/notify.sh banner "$ID" -`. When `IO_ADAPTER=github`, include a clickable link to the branch on GitHub so reviewers can follow along; other adapters omit it (there may be no GitHub remote).

Compute the branch URL only under the github adapter:

```bash
if [ "$IO_ADAPTER" = "github" ]; then
  BRANCH_URL="https://github.com/${GITHUB_REPOSITORY}/tree/${AGENTIC_BRANCH}"
fi
```

Two flavours:

**Fresh start** (no `.agentic-loop/<id>/.state` file exists):

```
🚀 Starting agentic-loop for #<issue>
Branch: [<branch>](<branch-url>)
Stage: spec
```

**Resume** (`.state` file exists — read state and current task from `tasks.json`):

```
🔄 Resuming agentic-loop for #<issue>
Branch: [<branch>](<branch-url>)
Stage: <state>
Current task: <id-or-none>
```

Post this **before** any subagent dispatch so the human always sees where the run started, even if it later exhausts turns silently.

## The Pipeline

```
                ┌─────────────────────────────────────────────┐
                │  STAGE 1: SPEC LOOP                         │
 task/issue ──▶ │  ingest → planner plans spec → interview    │
                │  → code-reviewer audits → fix → loop        │
                │  exit: spec-review has zero blockers        │
                └─────────────────────┬───────────────────────┘
                                      ▼
                ┌─────────────────────────────────────────────┐
                │  STAGE 2: PLAN LOOP                         │
                │  planner returns dispatch plan.             │
                │  → controller dispatches specialists        │
                |  → each returns TDD plan for their domain   │
                │  → planner synthesises unified plan.md      │
                │  → code-reviewer + specialists audit        │
                │  → fix → loop until zero blockers           │
                └─────────────────────┬───────────────────────┘
                                      ▼
                ┌─────────────────────────────────────────────┐
                │  STAGE 3: EXECUTE                           │
                │  for each task in tasks.json (sequential):  │
                │    dispatch implementer → TDD cycle         │
                │    spec-compliance review → fix loop        │
                │    code-quality review → fix loop           │
                │    quality gates: test + lint + tsc         │
                │    commit, mark done                        │
                └─────────────────────┬───────────────────────┘
                                      ▼
                ┌─────────────────────────────────────────────┐
                │  STAGE 4: SHIP                              │
                │  final code-reviewer pass on full diff      │
                │  raise PR, link issue, set state:in-pr      │
                └─────────────────────────────────────────────┘
```

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

## Stage 1 — Spec Loop

**Goal:** produce a spec that a specialist can plan from without follow-up questions.

**Entry:** No `.agentic-loop/<id>/.state` file exists (fresh start), or `.state == spec` (resuming after a CI pause or human-reply trigger).

1. **Ingest.** In interactive mode read `references/interactive-init.md` and run
   `scripts/init-run.sh` with the source file (snapshot inline requests to a temporary
   file first and pass stable `--title inline-spec`, unless a title was supplied),
   or resume using saved metadata. Honor its preflight, identity,
   branch collision, and resume rules. Map the returned run ID, branch, and base
   into `ID`, `AGENTIC_ISSUE` (legacy helper run-ID argument), `AGENTIC_BRANCH`,
   and `AGENTIC_BASE_REF` for each helper invocation; retain the optional real
   issue number separately for issue-only operations. A run ID is not necessarily
   a GitHub issue. The helper writes `source.md` and `run-context.json`; the
   controller persists them with run requirements in the ingest commit. In existing
   Claude CI, read supplied `AGENTIC_*` context and verify HEAD is on its branch.
   Do not run the interactive helper to reset a CI-prepared branch.
   `notify.sh` uses metadata's real issue for GitHub comments, falling back to
   file notifications for issue-less runs without changing PR adapter selection.
   For their blocking questions, preserve `open-questions.md` and `NEEDS_INPUT`
   before checkpointing; ask interactively and wait or yield for the answer.
   **Read `.agentic-loop.config.json` if present** (repo-specific base ref, quality gates, agent roster, risk categories — see `references/config.md`; absent ⇒ auto-detect defaults). **Resolve run tooling (fresh start only).** The invocation may carry flags — the raw string is delivered at the canonical parse site (the fenced token immediately below this list):

```
$ARGUMENTS
```

Parse `[--skill a,b] [--mcp x,y] [--subagent t1,t2]` once from Claude's
substituted line or the actual invocation/request in other harnesses. An empty or
literal placeholder is not data and does not erase user-supplied flags. Build the resolved set `{skills, mcps, specialists}` per `references/invocation-args.md` (skills/mcps = `dedup(flags ∪ config.required)`; `specialists` = a validated `--subagent` roster if present, **fully replacing** `agents.specialists`, else config, else the default single `general-purpose`), **validate every `--subagent` name before use** (resolvable + code-capable per that reference; surface failures via the available question interface interactively or `notify.sh blocked` headless — never the interview-exit path), and write `.agentic-loop/<id>/run-requirements.json`. If `run-requirements.json` already exists, reload it unchanged even when `.state` is absent; never re-parse invocation flags on resume. Treat helper `resumed:true` or an existing `.state` as a resume too. If either indicates a prior run but requirements are missing, stop for explicit ingest recovery instead of silently building a different configuration from the new request. The persisted file is the immutable run config and new invocation flags are ignored. This is the only args-substitution site; the `## Invocation Arguments` section is documentation that points here. **Pre-flight probe:** run `git status` and `command -v jq` once; require `gh auth status` when the resolved I/O adapter is `github`. Any failure → follow `BLOCKED_PERMISSION` immediately (see `references/status-handling.md`); do NOT enter Stage 1 work. Quality gates are resolved per-repo by `scripts/quality-gates.sh` (config or auto-detect) — there is no single required package manager. If `.agentic-loop/<id>/.state` exists, this is a **resume** — read it, post the Resume Banner, and skip directly to the indicated stage. Otherwise: use the interactive helper's existing source snapshot; in CI read the source (issue body via `gh issue view $ISSUE`, spec file, or inline task card) and save raw content to `.agentic-loop/<id>/source.md`, then check and write `.state = spec` before `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "chore(loop): ingest source + run config for #<issue>"` (this single ingest commit also captures the `run-requirements.json` written just above).
2. **Set label.** For a real GitHub issue under the GitHub adapter, set `state:planning` via `${AGENTIC_SKILL_DIR}/scripts/gh-label.sh`. Skip issue-only labels/comments for file/inline runs; never pass a synthetic run ID to a GitHub issue operation.
3. **Delegate to the planner for spec planning.** Dispatch a fresh configured planner child with `prompts/spec-planner.md` and `model: "opus"`. The planner returns a draft `spec.md` structured per its TDD format: Context · Goals · Non-goals · Architecture · Components · Test Strategy · Acceptance Criteria · Resolved Decisions · Open Questions · Risks. If the spec touches domain-specific research (domain mechanics, external APIs), the planner will include a `## Research Needed` section — **the controller** then dispatches the relevant configured specialist (from immutable `run-requirements.json.specialists`), **prepending the REQUIRED TOOLING block from `run-requirements.json`** (`references/invocation-args.md`) so research honours the run's required skills/MCPs, and passes findings back in the next spec draft iteration. The planner never dispatches specialists itself.
4. **Interview.** Collect questions from BOTH `open_questions[]` AND from `product_decisions_flagged[where !authorised_by_source]` in the spec-review.md. Also check `force_interview` — if true, an interview is mandatory even if both arrays are empty (this should not happen if spec-planner followed Step 0 correctly). In interactive mode, ask through the available question interface (batch independent questions). In headless mode, emit them as a single combined message via `${AGENTIC_SKILL_DIR}/scripts/notify.sh questions "$ID" open-questions.md`, write them to `open-questions.md`, **write `.state` = `spec` to `.agentic-loop/<id>/.state`** (mandatory — even a fresh-start run must write this file so the next trigger can resume; do not rely on `.state` absence as a proxy for "still in spec"), commit progress, and exit — under `IO_ADAPTER=github` the next issue-comment trigger resumes; under other adapters the harness re-invokes after dropping answers into `answers.md` (a `NEEDS_INPUT` sentinel + non-zero exit signals the pause). See `references/ci-mode.md §Interview Handshake` for the full gate logic.
5. **Merge answers.** Fold answers into `spec.md`. Remove the question from `open-questions.md`.
6. **Review — two passes.** Both run every iteration; neither replaces the other.
   1. **Structured review (drives the interview gate).** Dispatch a fresh configured reviewer carrying the bundled role with `prompts/spec-reviewer.md` and `model: "sonnet"`. It checks: placeholders, contradictions, ambiguity, missing test strategy, scope creep, requirements not traced to components. Output → `spec-review.md` with `{critical, important, minor}` lists **plus** the interview-driving fields (`open_questions`, `product_decisions_flagged`, `force_interview`). Save the reviewer's verdict **verbatim as the JSON object it returns** — never reformat it to prose or markdown, because the Stage 1→2 gate hook (`agentic-loop-check-state-transition.sh`) parses `verdict` and `force_interview` out of this file and will block the `plan` transition if it cannot read them. This pass is the source of the interview machinery — never skip it.
   2. **Validation pass (deeper pressure-test).** Run the bundled `references/validation/workflow.md` inline in this controller (see _Spec & Plan Validation_ below for the dispatch contract and why it must not be a subagent). Pass the explicit `spec.md` path, **forward the run's `--skill`/`--mcp` from `run-requirements.json`** (never `--subagent`) so the validation instances require the same tooling this run mandates, and direct its merged report to `.agentic-loop/<id>/spec-validation.md` — **not** `spec-review.md`, which the structured pass owns. It returns one `GO | REVISE | NO-GO` verdict plus a Blocker/Major/Minor findings ledger. Then `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "chore(loop): spec validation for #<issue>"`.
7. **Loop.** If `critical` or `important` in `spec-review.md` is non-empty, **OR the `spec-validation.md` verdict is `REVISE` or `NO-GO`**: check the eject flag first (see _Context Hygiene_), then re-delegate to the planner with BOTH the structured review and the validation Blockers/Majors as input, re-draft, re-review. Keep going. If the same issue recurs twice (per the recurrence trigger in _Red Flags_), escalate to the human — something in the source is under-specified.
8. **Exit.** Zero critical + zero important in `spec-review.md` **AND** `spec-validation.md` verdict is `GO` = spec locked. Update `.state` → `plan`. Run `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "chore(loop): lock spec for #<issue>"`.

See `references/spec-loop.md` for details.

## Stage Transition Gates — Hard Rules

The most common failure mode of past runs has been skipping a stage to "save turns". Do not. Each stage produces an artefact the next stage depends on. **Every gate below MUST be checked explicitly before `.state` advances.** Full gate criteria and the four Claude PreToolUse hooks that intercept supported operations live in `references/stage-gates.md`. The hooks enforce deterministically **only when installed and registered** in `.claude/settings.json` (see `setup/SETUP.md`; verify with `scripts/check-substrate.sh`); without active Claude interception, call the shared checks explicitly and enforce the remaining behavioral gates yourself. Codex always uses this controller-invoked mode.

- `spec` → `plan` — structured review approved (zero critical + important in `spec-review.md`), **`spec-validation.md` verdict is `GO`**, `open-questions.md` empty, every flagged product decision authorised, `force_interview === false`.
- `plan` → `implement` — structured review approved (zero critical + important in `plan-review.md`), **`plan-validation.md` verdict is `GO`**, `tasks.json` non-empty, every task has at least one test target.
- `implement` → `done` — every task `done` with both `spec_review_sha` AND `quality_review_sha` populated, resolved quality gates green on full branch, final-review approved.

If you ever find yourself moving from spec to implementation without `plan.md` and `tasks.json` on disk and reviewed, STOP — that is a process violation. Run the plan loop. The plan is the substrate the per-task TDD cycle lives on; without it the implementer has no failing-test contract to satisfy and review becomes ungrounded.

**Stage 2 is mandatory regardless of perceived task triviality** — a one-line change still gets a one-task plan, a plan review, and a per-task TDD cycle. The temptation to skip planning is strongest on "obvious" specs, and that is exactly when past CI runs went wrong.

## Stage 2 — Plan Loop

**Goal:** a single `plan.md` of bite-sized TDD tasks with exact file paths, test signatures + assertion bullets (NOT executable code), and verification steps.

**Entry:** Spec is locked — see _Stage Transition Gates_ and `references/stage-gates.md` (`spec → plan` gate) for the full conditions. (`.state == plan`)

1. **Dispatch plan.** Dispatch a fresh configured planner child with `prompts/impl-planner.md` (Mode A) — filling its `<roster>` block from `run-requirements.json`'s resolved `specialists` (a validated `--subagent` override when present, else `agents.specialists`, else the default single `general-purpose`; see `references/invocation-args.md` for the bare-type → `{type, owns}` adaptation, including the multi-type `owns:"code (planner allocates)"` placeholder) — plus `spec.md` and `model: "sonnet"`. The planner returns a `<dispatch_plan>` block conforming to the **Dispatch Plan Schema** in `references/plan-format.md`. The controller validates the JSON against that schema (non-empty `specialists`, every `agent_type` in the configured roster, no cycles in `depends_on`, every `research_needed[*].feeds_into` references a known specialist). If validation fails, re-dispatch the planner with the validation error. The planner does NOT dispatch specialists itself.
2. **Controller dispatches specialists.** Using the validated `<dispatch_plan>`, dispatch any `research_needed` agents first (sequentially or in parallel depending on `feeds_into` dependencies), then dispatch the `specialists` **in parallel** (queued within available child capacity), each prepended with `shared_context`. Each specialist receives: full `spec.md`, their scoped components, research findings if applicable, and `references/plan-format.md`. **Prepend the REQUIRED TOOLING block** (`references/invocation-args.md`) built from `run-requirements.json`'s `skills`/`mcps` — each skill to read/apply through the exposed interface with its reason, each MCP with a child-access verification instruction — only after confirming the specialist can use required tooling (the `--mcp` compatibility gate stops unsatisfied required work). Each returns a domain-scoped TDD plan. Do NOT pass `model:` on these dispatches — let each specialist inherit its harness-configured default.
3. **Synthesise.** Dispatch a fresh configured planner child with `prompts/impl-planner.md` (Mode B) and `model: "opus"`, passing `spec.md` and all collected domain plans inside `<domain_plans>` tags. The planner merges them into one `plan.md` using `references/plan-format.md`. Task granularity: 2–5 minute steps, exact file paths, test signatures + assertion bullets, expected failure mode, minimal implementation surface, expected pass criteria, commit message with `TDD:` line. No placeholders, no inline executable test code.
4. **Extract tasks.** Parse `plan.md` into `tasks.json`. Preserve dependency order.
5. **Review — two passes.** Both run every iteration.
   1. **Structured review.** Dispatch a fresh configured reviewer carrying the bundled role with `prompts/plan-reviewer.md` and `model: "sonnet"`. Also re-dispatch the domain specialists to sanity-check their slices (within available capacity, inherit harness defaults). Aggregate into `plan-review.md` with `{critical, important, minor}`.
   2. **Validation pass.** Run the bundled `references/validation/workflow.md` inline in this controller (see _Spec & Plan Validation_ below). Pass the explicit `plan.md` path as the spec-under-review plus `spec.md` for context, **forward the run's `--skill`/`--mcp` from `run-requirements.json`** (never `--subagent`), and direct its merged report to `.agentic-loop/<id>/plan-validation.md`. It returns one `GO | REVISE | NO-GO` verdict. Then `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "chore(loop): plan validation for #<issue>"`.
6. **Loop.** Check the eject flag first (see _Context Hygiene_), then fix until zero critical + important in `plan-review.md` **AND** `plan-validation.md` verdict is `GO`. Feed both the structured findings and the validation Blockers/Majors back into the re-plan. Same escalation rule as Stage 1.
7. **Exit.** Update `.state` → `implement`. Set label `state:implementing` only for a real GitHub issue. Run `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "chore(loop): lock plan for #<issue>"`.

See `references/plan-format.md` and `references/plan-loop.md`.

## Spec & Plan Validation

The spec-lock (Stage 1) and plan-lock (Stage 2) review steps each run a **second pass** through the `validating-specs` skill — a deeper, multi-instance pressure-test that augments (never replaces) the structured `code-reviewer` pass. The structured pass owns the interview-driving fields (`product_decisions_flagged`, `force_interview`, `open_questions`) and `*-review.md`; the validation pass owns the `GO`/`REVISE`/`NO-GO` verdict and `*-validation.md`. Both gate the stage exit.

**Dispatch contract — non-negotiable:**

1. **Read the bundled workflow inline.** Load
   `references/validation/workflow.md` in this controller. Its resource root is
   `references/validation/`: resolve its `references/` and `prompts/` beneath that
   directory. Do not spawn the workflow controller as a child. It directs this
   controller to dispatch fresh validators with the bundled rubric and prompts.
   No separately installed sibling skill or Skill tool is required.
2. **Pass explicit absolute paths.** Review `.agentic-loop/<id>/spec.md`, or
   `plan.md` with `spec.md` as context. Supply the resolved required skills/MCPs
   from `run-requirements.json`; never forward the implementation `--subagent`
   roster. Verify required tools in fresh validators before analysis.
3. **Redirect output.** Write the merged report to `spec-validation.md` or
   `plan-validation.md`, preserving the structured pass's separate `*-review.md`.
   Parse the final verdict and commit the artifact with `git-sync.sh`.
4. **Honor both gates.** Only `GO` can advance the stage. `REVISE`/`NO-GO` sends
   Blockers/Majors to the planner, then repeats drafting and both review passes.
   The recurrence escalation rule still applies. Machine checks do not enforce
   this free-form verdict; the controller must check it explicitly.
5. **Require a complete installation and fresh delegation.** Missing bundled
   resources, spawning capability, or required tooling is a setup failure.
   Report it and stop rather than skipping validation or self-reviewing.

## Stage 3 — Sequential Execution

**Goal:** every task in `tasks.json` merged green, reviewed, committed.

**Entry:** Plan is locked — see _Stage Transition Gates_ and `references/stage-gates.md` (`plan → implement` gate) for the full conditions. (`.state == implement`)

**Per-task review is mandatory.** Both spec-compliance AND code-quality reviews must run for every task. Skipping either one to "save turns" is a process violation — the loop's quality story rests on these two passes. If turn budget is tight, pause and resume rather than skip review. The presence of `spec_review_sha` and `quality_review_sha` on a task in `tasks.json` is the proof that review ran; missing values mean the task is not done.

**Reviewer-flagged issues must be fixed, not noted.** If a reviewer returns any `critical` or `important` finding, you re-dispatch the implementer with the finding attached and loop until the next review pass returns clean. Do not commit, do not advance the task to `done`, and do not move to the next task with unresolved blockers — that hides defects in the branch and they will surface as larger problems in final review or in production. `minor` findings can be logged in `progress.log` and addressed later.

For each `pending` task in dependency order:

0. **Context hygiene check.** In headless mode, check the eject flag before starting each task (see _Context Hygiene_ above). If set, flush and exit.
1. **Mark `in-progress`** in `tasks.json`. Set label `state:implementing` if not already.
2. **Dispatch implementer.** Fresh subagent via `prompts/task-implementer.md`. Do NOT pass `model:` — let the chosen specialist inherit its harness-configured default. Pass:
   - Full task text (copy from plan — do not make the subagent read the plan)
   - Relevant spec excerpt
   - Scene-setting context: where this task fits, what the prior task produced
   - Pick the right specialist agent type based on the task's domain
3. **Handle status.** Implementer returns one of `DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED | BLOCKED_PERMISSION | NEEDS_PRODUCT_DECISION`. Handle per `references/status-handling.md`. Never silently retry on the same model without changing something. `NEEDS_PRODUCT_DECISION` is the single exception to the Stage-3 no-interview rule — see Mid-Stage Question Protocol.
4. **Spec-compliance review (required).** Dispatch a fresh configured reviewer carrying the bundled role with `prompts/spec-compliance.md` and `model: "sonnet"` — verify the commit matches the task spec, nothing extra, nothing missing, and that the commit body contains the required `TDD:` line. If `critical` or `important` non-empty, re-dispatch the implementer with the findings and run review again. Loop until clean. Record the review-pass commit sha as `spec_review_sha` on the task.
5. **Code-quality review (required).** Dispatch a fresh configured reviewer carrying the bundled role with `prompts/quality-reviewer.md` and `model: "sonnet"` — correctness, security, maintainability, test coverage. Same fix-and-re-review loop. Record `quality_review_sha` on the task. Final review (Stage 4) provides a full-branch check; Claude uses its Opus tier there.
6. **Quality gates.** Run `${AGENTIC_SKILL_DIR}/scripts/quality-gates.sh` — it resolves the repo's gates from `.agentic-loop.config.json` or auto-detection (see `references/config.md`) and runs each. All must pass. If any fails, the implementer subagent is re-dispatched with the failure output. If it exits non-zero because **no** gate could be resolved, do not proceed — confirm via the available question interface (interactive) or post a blocking comment (CI), or set `"quality_gates": {}` in config to opt out explicitly. Never let an unverifiable repo ship silently. Do not edit tests to make them pass.
7. **Verify implementer commit.** The implementer owns the code commit (see `prompts/task-implementer.md` rule 3). Verify the SHA in their status report matches `git rev-parse HEAD` and the commit body has a `TDD:` line. If either is missing, re-dispatch the implementer — the controller does NOT commit code, only state files.
8. **Update state.** Mark task `done` in `tasks.json` only after both `spec_review_sha` AND `quality_review_sha` are populated and quality gates passed. Record `commit_sha`. Append learnings to `progress.log` per `references/progress-journal.md`. If a reusable pattern emerged, update the relevant `CLAUDE.md`. Run `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "chore(loop): finish <task-id> [#<issue>]"` so state files land on origin.
9. **Post progress.** In headless mode, emit a short progress update every N tasks (configurable, default 3) via `${AGENTIC_SKILL_DIR}/scripts/notify.sh progress "$ID" -`.

Never parallelise implementer subagents — conflicts cascade. Reviewers can run in parallel after the implementer commits.

See `references/execution-loop.md`.

## Stage 4 — Ship

**Entry:** Every task in `tasks.json` is `done` with both `spec_review_sha` AND `quality_review_sha` populated.

1. **Final review.** Dispatch the configured reviewer with the bundled review role (Claude tier: `model: "opus"`) against the full branch diff vs the base ref (`git diff "origin/${AGENTIC_BASE_REF:-main}...HEAD"` — use the `origin/` prefix because local branches do not exist on the Actions runner; in interactive mode the local-branch form also works) with `prompts/final-review.md`. Any critical/important issues → back into Stage 3 as a new fix task.
2. **Pre-PR gates.** Re-run `${AGENTIC_SKILL_DIR}/scripts/quality-gates.sh` on the full branch and `check-gates.sh pr-ready --run-dir "$RUN_DIR"`. Both must succeed before PR creation or SHIP_READY publication.
3. **Open PR.** Render the body deterministically with `${AGENTIC_SKILL_DIR}/scripts/render-pr-body.sh "$AGENTIC_ISSUE"` (reads `tasks.json` + `spec.md` + `plan.md`, so the body always matches committed state). Then, by adapter:
   - **`IO_ADAPTER=github`:** pipe into `gh pr create --base "$AGENTIC_BASE_REF" --title "<title>" --body-file -` (unchanged). See `references/pr-template.md`.
   - **Otherwise (`file`/`webhook`/`command`):** write the rendered body to `.agentic-loop/<id>/PR_BODY.md`, announce it via `notify.sh pr "$ID" .agentic-loop/<id>/PR_BODY.md`, and drop a `.agentic-loop/<id>/SHIP_READY` sentinel. Actually opening the PR needs a git remote + forge credentials the sandbox may not have — that is the host harness's job (see `references/ci-mode.md` / SETUP.md "out of scope"). Emit COMPLETE once the body + sentinel are committed.
4. **Label.** For a real GitHub issue only, set `state:in-pr` and remove `state:implementing`.
5. **Reset auto-resume counter.** `rm -f ".agentic-loop/${AGENTIC_ISSUE}/resume-attempts"` then `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "chore(loop): reset resume-attempts on PR open for #${AGENTIC_ISSUE}"`. Otherwise a future re-run on the same issue inherits the cap immediately. See `references/auto-resume-config.md`.
6. **Emit completion.** Output `<loop-state>COMPLETE</loop-state>` followed by the PR URL and a one-paragraph summary.

### Stage 4 hard rules

- **Never write `.state = done` from this skill.** `state:done` is owned by the merge pipeline (see the table below). The state-transition gate now blocks both `Write` and `Bash` redirects into `.state` for the `done` transition; the cleaner contract is that the skill stops touching `.state` once `gh pr create` succeeds. Past runs that wrote `done` prematurely left the remote branch in a phantom-complete state with no PR.
- **Verify before emitting `<loop-state>COMPLETE</loop-state>`.** Under `IO_ADAPTER=github`, run `gh pr list --head "$AGENTIC_BRANCH" --state open --json number --jq 'length'` and confirm it returns `≥ 1`; if `gh pr create` returned non-zero or the count is zero, do **not** emit COMPLETE — escalate via `${AGENTIC_SKILL_DIR}/scripts/notify.sh blocked "$ID" -` and exit non-zero so the workflow's failure-comment branch fires. Under other adapters, confirm `.agentic-loop/<id>/PR_BODY.md` and `SHIP_READY` were written and committed before emitting COMPLETE.
- **Order is non-negotiable:** final review → quality gates → `gh pr create` → label flip → completion marker. Any earlier step failing means stop, do not advance.

## Issue State Machine

For runs attached to a real GitHub issue, label transitions live in `references/issue-state-machine.md`. The skill drives transitions up to `state:in-pr`; `state:done` is owned by the merge pipeline.

## Red Flags — Stop and Escalate

- **Recurrence trigger** — escalate to the human when the same `area`/`task_id` is flagged in `critical` or `important` across two consecutive review iterations on the same stage. This is the single deterministic recurrence rule; volume heuristics ("> 5 important", "> 3 unrelated bugs", "> 2 PRODUCT-class") were removed because no counter state existed to enforce them.
- Quality gates fail for reasons unrelated to the current task → infrastructure problem; escalate.
- Implementer returns `BLOCKED` with a plan-level complaint → plan needs revision; jump back to Stage 2 for the affected tasks only.
- Branch diverges from the resolved base by more than a day of merges → rebase before continuing; abort if rebase conflicts are non-trivial.
- Any subagent proposes editing tests to make production code pass → reject, mark task blocked, escalate.
- A subagent reports a permission denial or required tool unavailable (including Claude `tool_use_error`) → treat as `BLOCKED_PERMISSION`. Do not retry. Do not improvise around it. Follow the permissions handshake (`references/permissions-handshake.md`).
- A subagent surfaces an open question while `.state == implement` → DO NOT post to the human. Mark the task `blocked`, log the spec gap to `progress.log`, and continue with another task or jump to plan revision per `references/plan-loop.md`. Implementation-time questions mean the spec/plan was incomplete.
- About to commit a task without `spec_review_sha` AND `quality_review_sha` populated → STOP. The two-stage review is non-negotiable; back up, run the missing review, fix anything it flags, only then commit and advance.
- About to advance `.state` from `spec` directly to `implement`, or to start dispatching task implementers without `plan.md` and `tasks.json` on disk → STOP. Run the plan loop. The plan is the contract the implementer satisfies; without it there is no TDD, no review baseline, and no progress accounting.
- A reviewer returns `critical` or `important` findings and you are tempted to "log and move on" → STOP. Re-dispatch the implementer with the findings until review is clean. Only `minor` findings may be logged for follow-up.
- You have surfaced an open question in headless mode and are tempted to resolve it with a "conservative default" / "documented assumption" and keep going (especially with a "confirm before merge" note) → STOP. That is **silent-invention** (see _Interview Discipline_): notify, commit, and exit; `.state` stays `spec`/`plan`. The state-transition gate hook enforces the same rule deterministically when registered.

## Files and Prompts

Grouped by stage. See each file for full content.

- **Stage 1 (spec):** `prompts/spec-planner.md`, `prompts/spec-reviewer.md`, `references/spec-loop.md`.
- **Stage 2 (plan):** `prompts/impl-planner.md` (Mode A + B), `prompts/plan-reviewer.md`, `references/plan-format.md`, `references/plan-loop.md`.
- **Stage 3 (execute):** `prompts/task-implementer.md`, `prompts/spec-compliance.md`, `prompts/quality-reviewer.md`, `references/execution-loop.md`, `references/status-handling.md`, `references/tdd.md`, `references/progress-journal.md`.
- **Stage 4 (ship):** `prompts/final-review.md`, `references/pr-template.md`.
- **Cross-cutting:** `references/config.md` (the optional `.agentic-loop.config.json` contract), `references/ci-mode.md`, `references/permissions-handshake.md`, `references/auto-resume-config.md`, `references/context-hygiene.md`, `references/interview-protocol.md`, `references/model-tiering.md`, `references/stage-gates.md`, `references/issue-state-machine.md`.
- **Bundled validation:** `references/validation/workflow.md` plus its local resources, generated from the canonical validating-specs skill; no sibling installation is required.
- **Setup / substrate:** `setup/SETUP.md` (how to install the skill in any repo — env contract, repo variables, hooks + registration, `validating-specs` dependency, optional config, local-only path), `setup/settings.snippet.json` (hook-registration block), `setup/hooks/` (the 3 gate-hook install templates), `setup/agentic-loop.yml` (CI workflow template). Config contract: `references/config.md` (the optional `.agentic-loop.config.json`).
- **Scripts:** `${AGENTIC_SKILL_DIR}/scripts/quality-gates.sh` (resolves + runs the repo's quality gates — config or auto-detect; see `references/config.md`), `${AGENTIC_SKILL_DIR}/scripts/check-substrate.sh` (probe: are the gate hooks registered, i.e. deterministic vs model-only enforcement?), `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh` (only place that mutates git state from the loop), `${AGENTIC_SKILL_DIR}/scripts/lib-mode.sh` (interactivity resolver → `interactive`|`headless`; single source of truth for mode), `${AGENTIC_SKILL_DIR}/scripts/notify.sh` (harness-agnostic human I/O — dispatches to `IO_ADAPTER`; use this, not `gh-comment.sh`, for all banners/questions/progress/escalations), `${AGENTIC_SKILL_DIR}/scripts/gh-comment.sh` (the `github` adapter's backend; auto-prepends `@$AGENTIC_AUTHOR` — do not double-tag), `${AGENTIC_SKILL_DIR}/scripts/gh-label.sh`, `${AGENTIC_SKILL_DIR}/scripts/render-pr-body.sh`, `${AGENTIC_SKILL_DIR}/scripts/precompact-flush.sh`, `${AGENTIC_SKILL_DIR}/scripts/postooluse-context-check.sh`.

## Remember

- The planner plans and synthesises; **you dispatch specialists** — never delegate Agent calls to the planner.
- TDD everywhere — no production line written before a failing test.
- Fresh subagent per task, precise context, no session bleed.
- Loops exit on zero critical + zero important. "Minor" goes in `progress.log` for follow-up.
- Persist progress every iteration — CI and context-window interruptions are expected.
- Stop at the PR. Do not merge. Humans or CI merge.
