# Execution Loop — Detailed Protocol

## Entry

`.state` == `implement`. `plan.md` and `tasks.json` locked and committed. Feature branch checked out.

## Per-Task Cycle

For each `pending` task in dependency order:

### 1. Select & mark

Pick the next task whose `deps` are all `done`. Capture the starting commit so spec-compliance and quality reviewers can diff just this task's changes:

```bash
TASK_START_SHA=$(git rev-parse HEAD)
```

Record `task_start_sha` on the task in `tasks.json` alongside `status: "in-progress"`. Then commit:

```
chore(loop): start <task-id> <task-title> [#<issue>]
```

### 2. Dispatch implementer

Fresh subagent. Use `prompts/task-implementer.md`. Pick the `subagent_type` by matching `task.domain` to the `type` of the `agents.specialists` entry that owns that domain; if no entry matches (or `agents.specialists` is unset), use `general-purpose`. Because the planner set `task.domain` in Mode A from the same configured roster, the mapping is 1:1 by construction — Stage 3 routes on the same roster Stage 2 planned with.

Pass to the implementer:

- Full task text (literal copy from `plan.md`)
- Task ID and title
- Relevant spec excerpt (components this task touches)
- Previous task summary (what just landed)
- Working branch name
- Status vocabulary (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED)

Never ask the implementer to read `plan.md` — the controller extracts and passes the exact task text. This keeps the subagent's context focused.

### 3. Handle status

See `status-handling.md`. If `DONE` or `DONE_WITH_CONCERNS` (concerns addressed), proceed to review.

### 4. Spec-compliance review (REQUIRED)

Dispatch `code-reviewer` with `prompts/spec-compliance.md`. Inputs:

- Task text
- `git diff <task-start-sha>..HEAD`
- Files touched

Verdict must confirm: all spec items implemented, no scope creep, no renames from plan, no silent skips. If `critical` or `important` non-empty, re-dispatch the implementer (same subagent type) with the review attached. Loop until both lists are empty. Then record the head sha as `spec_review_sha` on the task in `tasks.json`.

This pass is non-skippable. A task without `spec_review_sha` is incomplete, regardless of how green its tests look.

### 5. Code-quality review (REQUIRED)

Dispatch `code-reviewer` with `prompts/quality-reviewer.md`. Inputs:

- `git diff <task-start-sha>..HEAD`
- Security sensitivity flags for the domain (backend → authz/injection/rate-limit; frontend → XSS/output-escaping/auth-state; data → migration safety/PII; CLI → arg escaping/EPIPE; plus any domain-specific risks the configured reviewer knows)

Same fix-and-re-review loop until clean. Record `quality_review_sha`.

If turn budget cannot fit both reviews + their fix loops, prefer to checkpoint and exit so the next CI run resumes mid-task review — never advance the task status to `done` with either review unrecorded.

### 6. Quality gates

Run `scripts/quality-gates.sh`. If any step fails:

- Capture the failure output.
- Re-dispatch the implementer with the failure as the task context.
- Do not modify tests to make them pass (the review loop catches this too).

### 7. Verify implementer commit

The implementer owns the code commit (see `prompts/task-implementer.md` rule 3). The controller does NOT commit code. Verify:

1. The implementer's status report contains a commit SHA.
2. `git rev-parse HEAD` matches that SHA.
3. The commit body contains a `TDD:` line (the spec-compliance reviewer will have already flagged a missing line, but re-check here as a belt-and-braces gate).

If any of these fail, re-dispatch the implementer with the gap as context. Do NOT paper over a missing commit by committing for them — that loses the test-first proof.

`type` in the implementer's commit message ∈ `feat|fix|chore|refactor|docs|test|perf`. The controller's subsequent state-file commit (step 8) goes through `scripts/git-sync.sh commit` and pushes atomically so the next CI run can resume.

### 8. Update state

- Mark task `done` in `tasks.json`, set `commit_sha`. **The `agentic-loop-check-tasks-json.sh` PreToolUse hook will reject this write unless both `spec_review_sha` and `quality_review_sha` are populated on the same task.** A block here means a review pass is missing — go run it, do not retry.
- Append to `progress.log` per `progress-journal.md`.
- If a reusable pattern emerged, update the relevant `CLAUDE.md`.
- Run `scripts/git-sync.sh commit "chore(loop): finish <task-id> [#<issue>]"`.

### 9. Post progress (CI)

Every N tasks (default 3, or on stage boundary), post a progress comment on the issue listing:

- Completed task IDs + titles
- Current task ID
- Remaining count
- Link to latest commit

## Constraints

- **Never parallelise implementer subagents.** File conflicts cascade and the review loop cannot distinguish which agent owns which change.
- **Reviewers may run in parallel** after the implementer commits — they read-only.
- **Never let the implementer skip tests.** Iron Law from `tdd.md` applies here too.
- **Never edit `plan.md` mid-execute.** If the plan is wrong, jump back to the plan loop for that task.
