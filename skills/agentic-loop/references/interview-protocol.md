# Mid-Stage Question Protocol

Open-questions to the human are allowed **only** when `.state` is `spec` or `plan`. Once `.state` is `implement` (Stage 3) or `done` (Stage 4), the human has already answered everything they needed to. No more interviews — questions during implementation indicate the spec or plan was incomplete and must round-trip through review, not through the human inbox.

## Stage 1 / Stage 2 (`.state ∈ {spec, plan}`)

The operative bar for what counts as an open question is the two-alternatives test defined in `prompts/decision-rules.md` and audited in `prompts/spec-reviewer.md` check 13 — not the planner's confidence that it knows the answer. If the planner or reviewer can name a second defensible option and `source.md` does not literally authorise the chosen one, it is an open question, regardless of category (product, architectural, library, or threshold).

**Surfacing a question is a full stop, not a checkpoint you pass through.** In headless mode the absence of a human means the run *pauses and exits* — it does NOT mean you are now authorised to pick the answer. Adopting a "conservative default", a "documented assumption", or a "safe" choice and then continuing to plan/implement/ship is the exact silent-invention failure this protocol prevents; "a human will confirm before merge" does not license proceeding without the answer. This binds hardest for a *load-bearing decision* (see `prompts/decision-rules.md`): once one is surfaced, `.state` stays `spec`/`plan` and the run exits — it never reaches `implement` or opens a PR under the unanswered decision.

**The interview fires** when any of these holds on the latest `spec-review.md` (or `plan-review.md`):

- `force_interview === true`;
- `open_questions[]` is non-empty;
- any `product_decisions_flagged[]` entry has `authorised_by_source: false`.

An empty `open_questions[]` alone does not clear the gate; all three must be clear.

When the interview fires, or a subagent or you hit any other question that needs human input (ambiguous spec line, missing acceptance criterion, any decision-fork hit):

1. Write every question to `.agentic-loop/<id>/open-questions.md` in the shape of §Open-questions file: each `open_questions[]` entry, plus each unauthorised `product_decisions_flagged[]` entry as a Confirm question.
2. Write the current stage (`spec` or `plan`) to `.agentic-loop/<id>/.state`, also on a fresh-start run where `.state` did not exist: the next trigger resumes from this file, and a missing `.state` reads as an un-ingested issue.
3. Interactive: ask through the available question interface, batching independent questions, and hold dependent work until the human answers. Headless: emit the file via `"${AGENTIC_SKILL_DIR}/scripts/notify.sh" questions "$ID" .agentic-loop/<id>/open-questions.md`; the adapter picks the transport (issue comment, file, webhook, or command).
4. `"${AGENTIC_SKILL_DIR}/scripts/git-sync.sh" commit "chore(loop): pause for open questions on #<issue>"`.
5. Headless adapter-aware exit: `github` → `exit 0`; other adapters → write `.agentic-loop/<id>/NEEDS_INPUT` (containing the reason) and `exit 78`, the needs-input code a non-GitHub harness detects without parsing logs.

On resume, read the answers: under `github`, from the next `issue_comment` by a human (not the bot) on the same issue; under other adapters, from `.agentic-loop/<id>/answers.md` or answers written inline under each question in `open-questions.md`. Fold each answer into where it belongs (`spec.md`, `plan.md`, or a task's context), close the file per §Open-questions file, and continue the stage. If the answers do not parse against the numbered questions, re-notify with the expected reply format and pause again.

## Open-questions file

`.agentic-loop/<id>/open-questions.md` is the interview's only record. The gate hooks (`lib-gates.sh`) read it as **open** when it has any byte and **closed** when it is empty or absent, so it blocks both the `plan`/`implement` transitions and `gh pr create` while open.

Shape, one numbered line per question:

```markdown
1. [spec] <question>
2. [plan][T3] <question>
3. [spec] Confirm: <decision>? Suggested default (if any): <X>
4. [PRODUCT][T5] <question>

Reply with one answer per number, e.g. `1. <answer>`.
```

- The tag names the originating stage (`spec` or `plan`), plus `[<task-id>]` when a task raised it. A Stage-3 product decision uses `[PRODUCT][<task-id>]` (see `status-handling.md` §NEEDS_PRODUCT_DECISION).
- An unauthorised product decision becomes a `Confirm:` question.
- The last line is the reply instruction.

Close it once every answer is folded in: truncate it to zero bytes (`: > .agentic-loop/<id>/open-questions.md`) or `rm` it, and clear `answers.md` the same way. A closed file holds zero bytes; a header or "all resolved" note counts as an open interview and blocks `gh pr create`.

## Stage 3 (`.state == implement`) — NO interviews, ONE exception

If a subagent surfaces an ambiguity during implementation, the spec/plan is incomplete. Do NOT post an issue comment. Instead:

1. Mark the task `blocked` in `tasks.json` with the ambiguity recorded under `blocker_reason`.
2. Append a single line to `progress.log`: `<task-id>: blocked — spec gap: <one-sentence summary>`.
3. Skip to the next task whose dependencies are still satisfied. If none exist, jump to plan-loop revision per `plan-loop.md` (which IS allowed to escalate to the human because it transitions `.state` back to `plan`).
4. Never silently guess. Never improvise the missing detail.

This rule keeps long-running implementation runs from pinging the human every few minutes with questions that should have been resolved in spec/plan.

**The one exception: `STATUS: NEEDS_PRODUCT_DECISION`.** If the implementer surfaces a *load-bearing decision* (see `prompts/decision-rules.md`), the loop IS allowed to interview the human directly during Stage 3 — because by definition the spec/plan was wrong to resolve it, and re-running the spec loop just to re-ask is wasteful. Follow `status-handling.md §NEEDS_PRODUCT_DECISION`: persist the `[PRODUCT]` question, notify, and pause; only real GitHub issues receive labels/comments. Issue-less runs retain local notification and pause artifacts. All other ambiguities still go through spec/plan revision, not the human inbox.

## Permission denials

Follow `permissions-handshake.md` instead — same shape, denial-specific template. Permission denials are treated as infra-level blockers, not product questions, so they pause regardless of `.state`.
