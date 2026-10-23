# Execution Loop (Stage 3)

**Goal:** every task in `tasks.json` green, reviewed and committed.

**Entry:** `.state == implement`: the `plan` → `implement` gate in `stage-gates.md` held, `plan.md` and `tasks.json` are locked and committed, and the feature branch is checked out.

**Per-task review is mandatory.** Both the spec-compliance and the code-quality review run for every task; `spec_review_sha` and `quality_review_sha` on the task in `tasks.json` are the proof that they ran, and a task missing either is not done, however green its tests look. When the turn budget cannot fit both reviews and their fix loops, checkpoint and exit so the next run resumes mid-task review.

**Reviewer-flagged issues are fixed, not noted.** On any `critical` or `important` finding, re-dispatch the implementer with the finding attached and loop until the next review pass returns clean; the task stays uncommitted, not `done`, and the next task waits. Log `minor` findings in `progress.log` for follow-up.

## Per-Task Cycle

For each `pending` task in dependency order:

### 0. Context hygiene check

In headless mode, check the eject flag before starting each task (SKILL.md §Context hygiene). If it is set, flush and exit.

### 1. Mark `in-progress` and capture the base

Pick the next task whose `deps` are all `done`. Run `TASK_START_SHA=$(git rev-parse HEAD)`. Write `status: "in-progress"` and `task_start_sha` to the task in `tasks.json`. For a real GitHub issue, set label `state:implementing` if it is not already set. Commit:

```
chore(loop): start <task-id> <task-title> [#<issue>]
```

Done when `jq -r '.tasks[] | select(.id=="<id>") | .task_start_sha' .agentic-loop/<id>/tasks.json` prints a SHA.

### 2. Dispatch implementer

Create a fresh child through `dispatch.md` with `prompts/decision-rules.md` prepended to `prompts/task-implementer.md`. Omit `model:` so the chosen specialist inherits its harness default. Match `task.domain` to the immutable `run-requirements.json.specialists` roster used by Stage 2. Do not reread config or substitute a generic worker when an explicit roster entry is unavailable. Missing ownership is a plan error: return to the planner. The default generic roster is resolved only at ingest. Include the REQUIRED TOOLING block and verify required child capabilities before dependent work.

Pass to the implementer:

- Full task text (literal copy from `plan.md`)
- Task ID and title
- Relevant spec excerpt (components this task touches)
- Scene-setting context: where this task fits, and what the previous task landed
- Working branch name
- Status vocabulary: the six tokens in `status-handling.md` (the prompt already lists them)

Never ask the implementer to read `plan.md` — the controller extracts and passes the exact task text. This keeps the subagent's context focused.

### 3. Handle status

The implementer returns one of the six tokens in `status-handling.md`; handle each per that file, and change something before any retry. `NEEDS_PRODUCT_DECISION` is the one Stage-3 interview (`interview-protocol.md`). If `DONE` or `DONE_WITH_CONCERNS` (concerns addressed), proceed to review.

### 4. Spec-compliance review (REQUIRED)

Dispatch a fresh configured reviewer carrying the bundled role with `prompts/spec-compliance.md` and `model: "sonnet"`. Inputs:

- Task text
- `task_start_sha`, and `git diff <task_start_sha>..HEAD`
- Files touched

Verdict must confirm: all spec items implemented, no scope creep, no renames from plan, no silent skips, and a `TDD:` line in the commit body. If `verdict` is `needs-changes` (any issue with severity `critical` or `important`), re-dispatch the implementer (same subagent type) with the review attached. Loop until `verdict` is `approved`. Then record the head sha as `spec_review_sha` on the task in `tasks.json`.

### 5. Code-quality review (REQUIRED)

Dispatch a fresh configured reviewer carrying the bundled role with `prompts/quality-reviewer.md` and `model: "sonnet"`: correctness, security, maintainability, test coverage. Inputs:

- `task_start_sha`, and `git diff <task_start_sha>..HEAD`
- Security sensitivity flags for the domain (backend → authz/injection/rate-limit; frontend → XSS/output-escaping/auth-state; data → migration safety/PII; CLI → arg escaping/EPIPE; plus any domain-specific risks the configured reviewer knows)

Same fix-and-re-review loop until `verdict` is `approved`. Record `quality_review_sha`. The Stage 4 final review adds a full-branch check; Claude uses its Opus tier there.

### 6. Quality gates

Run `${AGENTIC_SKILL_DIR}/scripts/quality-gates.sh`; it resolves the repo's gates from `.agentic-loop.config.json` or auto-detection (`config.md`) and runs each. All must pass. If any step fails:

- Capture the failure output.
- Re-dispatch the implementer with the failure as the task context.
- Keep the tests as written; fix the production code (the review loop catches edited tests too).

If it exits non-zero because **no** gate could be resolved, hold the task: confirm through the interview protocol (the interactive question interface, or a blocking `notify.sh` message headless), or set `"quality_gates": {}` in config to opt out explicitly. An unverifiable repo never ships silently.

### 7. Verify implementer commit

The implementer owns the code commit (see `prompts/task-implementer.md` rule 3); the controller commits only state files. Verify:

1. The implementer's status report contains a commit SHA.
2. `git rev-parse HEAD` matches that SHA.
3. The commit body contains a `TDD:` line (the spec-compliance reviewer will have already flagged a missing line, but re-check here as a belt-and-braces gate).

If any of these fail, re-dispatch the implementer with the gap as context. Leave the code commit to the implementer even then: a controller commit loses the test-first proof.

`type` in the implementer's commit message ∈ `feat|fix|chore|refactor|docs|test|perf`. The controller's subsequent state-file commit (step 8) goes through `scripts/git-sync.sh commit` and pushes atomically so the next CI run can resume.

### 8. Update state

- Mark task `done` in `tasks.json` only once both `spec_review_sha` and `quality_review_sha` are populated and the quality gates passed; set `commit_sha`. Run both shared `tasks` and `tdd` checks on the proposed document before writing. Registered Claude hooks additionally intercept supported writes; Codex requires these explicit controller calls. A block here means a review pass is missing — go run it, do not retry.
- Append to `progress.log` per `progress-journal.md`.
- If a reusable pattern emerged, update the applicable repository instructions (`AGENTS.md` or `CLAUDE.md`).
- Run `scripts/git-sync.sh commit "chore(loop): finish <task-id> [#<issue>]"`.

### 9. Post progress

In headless mode, every N tasks (default 3) and at each stage boundary, pipe a progress message into `"${AGENTIC_SKILL_DIR}/scripts/notify.sh" progress "$ID" -` listing:

- Completed task IDs + titles
- Current task ID
- Remaining count
- Link to latest commit

## Constraints

- **Run one implementer at a time.** Parallel implementers cascade file conflicts, and the review loop cannot tell which agent owns which change.
- **Reviewers may run in parallel** after the implementer commits; they are read-only.
- **Every task ships with its tests.** The Iron Law from `tdd.md` applies here too.
- **`plan.md` is fixed during execution.** If the plan is wrong, jump back to the plan loop for that task.

## Exit

Exit when every task in `tasks.json` is `done` with both `spec_review_sha` and `quality_review_sha` populated: the artefacts of the `implement` → PR open gate in `stage-gates.md`. `.state` stays `implement`. Continue with `ship.md`.
