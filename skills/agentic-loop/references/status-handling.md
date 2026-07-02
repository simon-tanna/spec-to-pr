# Handling Implementer Status

Implementer subagents end with one of four status tokens. Handle each deliberately — never silently retry.

## DONE

Work complete, tests pass, committed. Proceed to spec-compliance review.

## DONE_WITH_CONCERNS

Work complete but the implementer flagged doubts. Read the concerns.

- **Correctness / scope concerns:** address before review. Re-dispatch if needed.
- **Observations** (e.g. "this file is getting large"): record in `progress.log` and proceed to review.

Never ignore the concerns.

## NEEDS_PRODUCT_DECISION

Implementer hit a load-bearing product call (data custody/ownership, access control, an irreversible/destructive operation, billing/fees, data retention/privacy, a security trust boundary, external-service trust, or a breaking public-contract change — plus any configured `risk_categories`). Treat exactly like a Stage 1/2 open question — but unlike `NEEDS_CONTEXT`, do NOT supply an answer yourself; the controller is also not authorised to decide.

Protocol:

1. Mark the task `blocked` in `tasks.json` with `blocker_reason: "needs product decision: <one-sentence summary>"`.
2. Append the question to `.agentic-loop/<id>/open-questions.md` prefixed `[PRODUCT][<task-id>]`.
3. Add label `state:needs-decision` via `scripts/gh-label.sh`.
4. Emit a single message via `scripts/notify.sh blocked "$ID" -` using the Open-Questions template.
5. In interactive mode, also raise via `AskUserQuestion`.
6. `scripts/git-sync.sh commit "chore(loop): pause for product decision on #<issue>"`. Then adapter-aware exit: `github` → `exit 0`; other adapters → drop `.agentic-loop/<id>/NEEDS_INPUT` and `exit 78`.

This is the ONE Stage-3 question type that IS allowed to escalate to the human — because by definition the spec/plan was wrong to resolve it, and the cost of guessing is high. All other Stage-3 ambiguities still go through the spec/plan revision path, not the human inbox.

## NEEDS_CONTEXT

The implementer cannot proceed without information not provided. Supply the missing context and re-dispatch with the **same** subagent type.

Common causes:

- The task referenced a type/function defined in an earlier task that the implementer could not locate — include the file path and excerpt.
- External dependency: library docs, API schema, contract ABI — fetch and include.
- Product decision: ambiguity in the spec — escalate to human in interactive mode; emit a question via `scripts/notify.sh` in headless mode.

## BLOCKED

The implementer cannot complete the task as written. Diagnose:

1. **Context problem** → provide more context, re-dispatch same model.
2. **Reasoning problem** (task harder than expected) → re-dispatch with a more capable model/agent type.
3. **Task too large** → split into sub-tasks, update `plan.md` and `tasks.json`, start with the first sub-task.
4. **Plan is wrong** (the approach itself does not work) → jump back to the plan loop for this task, mark the task `blocked`, escalate.

On every `BLOCKED` return, increment `blocker_count` on the task in `tasks.json` (initialise to 0 when the task is first created). If `blocker_count >= 2`, treat as a plan-level problem and jump back to the plan loop — the counter makes the "two consecutive" rule enforceable rather than vibes-based.

**Reset timing.** Reset `blocker_count` to 0 **when the task transitions out of `blocked` back into `pending` or `in-progress` as a result of a plan-loop revision** — i.e. `plan.md` was edited to address the blocker and the task is being retried under the new plan. Do NOT reset on the `done` transition. The historical `blocker_count` is a useful audit trail at completion: a task that reaches `done` with `blocker_count >= 2` and no intervening reset means the controller skipped plan-loop revision. The `agentic-loop-check-tasks-json.sh`, `agentic-loop-check-state-transition.sh`, and `agentic-loop-check-pr-ready.sh` hooks all read this field and reject the corresponding write/transition/PR-create when they see this pattern — making the rule structurally enforced rather than convention.

## BLOCKED_PERMISSION

The implementer or any subagent hit a `tool_use_error` of the form
`Claude requested permissions to use <Tool>, but you haven't granted it yet.`
This is unrecoverable inside the run — only the human can grant the permission.

Protocol:

1. Capture the denied tool name and the call's `description` (and a short summary
   of _why_ the subagent reached for it, if obvious from the prior thinking step).
2. Append to `.agentic-loop/<id>/blockers.md`:
   - timestamp, stage, task id (if any), denied tool, reason
3. Emit a single message via `scripts/notify.sh blocked "$ID" -` with the format
   in `references/permissions-handshake.md` — explicitly listing the tool to
   grant and how (workflow `--allowed-tools`, settings.json permission, or
   `additional_permissions:` input).
4. `scripts/git-sync.sh commit "chore(loop): pause for permission grant on #<issue>"`
5. Adapter-aware exit: `github` → `exit 0`; other adapters → drop
   `.agentic-loop/<id>/NEEDS_INPUT` and `exit 78`. Do NOT retry the denied tool.
   Do NOT silently fall back to a different tool unless the alternative is
   explicitly equivalent.

On the next `issue_comment` trigger:

1. Re-check the perm by attempting the original call once.
2. If it succeeds, delete the entry from `blockers.md` and resume.
3. If it still fails, post a follow-up comment ("permission still denied — workflow may need redeploy") and exit.

Two consecutive `BLOCKED_PERMISSION` for the same tool = workflow misconfig; escalate.

## Never

- Retry the same subagent type on the same input after `BLOCKED` without changing something.
- Silently drop a `DONE_WITH_CONCERNS` flag.
- Proceed to review with `NEEDS_CONTEXT` unaddressed.
- Retry a tool that returned `tool_use_error: ... permissions ...` without first pausing for human grant.
- Resolve a `NEEDS_PRODUCT_DECISION` by guessing or by re-dispatching with extra context. The decision belongs to the human.
