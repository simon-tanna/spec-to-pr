# Mid-Stage Question Protocol

Open-questions to the human are allowed **only** when `.state` is `spec` or `plan`. Once `.state` is `implement` (Stage 3) or `done` (Stage 4), the human has already answered everything they needed to. No more interviews — questions during implementation indicate the spec or plan was incomplete and must round-trip through review, not through the human inbox.

## Stage 1 / Stage 2 (`.state ∈ {spec, plan}`)

The operative bar for what counts as an open question is the "two reasonable alternatives" rule defined in `prompts/spec-planner.md` §Step 0.5 and audited in `prompts/spec-reviewer.md` check 13 — not the planner's confidence that it knows the answer. If the planner or reviewer can name a second defensible option and `source.md` does not literally authorise the chosen one, it is an open question, regardless of category (product, architectural, library, or threshold).

When a subagent or you encounter a question that requires human input (product decision, ambiguous spec line, missing acceptance criterion, any decision-fork hit), do not guess and do not block on `AskUserQuestion` (unavailable in headless mode). Instead:

1. Append the question to `.agentic-loop/<id>/open-questions.md`, prefixed with the originating stage and (if any) task id.
2. Emit them via `scripts/notify.sh questions "$ID" .agentic-loop/<id>/open-questions.md` using the Open-Questions template in `ci-mode.md` (the adapter picks the transport — issue comment, file, webhook, or command).
3. `scripts/git-sync.sh commit "chore(loop): pause for open questions on #<issue>"`
4. Adapter-aware exit: `github` → `exit 0`; other adapters → drop `.agentic-loop/<id>/NEEDS_INPUT` and `exit 78` (see `ci-mode.md §Interview Handshake`).

On resume (an `issue_comment` trigger under `github`, or a harness re-invocation with `.agentic-loop/<id>/answers.md` under other adapters), parse the reply against `open-questions.md`, fold answers into wherever they belong (`spec.md` / `plan.md` / a specific task's context), and **clear the questions file mechanically** (also clear `answers.md` if present):

- Either truncate it to zero bytes (`: > .agentic-loop/<id>/open-questions.md`) or `rm` it.
- **Never** write a placeholder, header, or "All questions resolved" summary into the file. The PR-ready hook (`agentic-loop-check-pr-ready.sh`) treats any byte as an open interview and will block `gh pr create` — past runs lost ~3 minutes of token budget at Stage 4 because of placeholder text.

Then continue the stage.

## Stage 3 (`.state == implement`) — NO interviews, ONE exception

If a subagent surfaces an ambiguity during implementation, the spec/plan is incomplete. Do NOT post an issue comment. Instead:

1. Mark the task `blocked` in `tasks.json` with the ambiguity recorded under `blocker_reason`.
2. Append a single line to `progress.log`: `<task-id>: blocked — spec gap: <one-sentence summary>`.
3. Skip to the next task whose dependencies are still satisfied. If none exist, jump to plan-loop revision per `plan-loop.md` (which IS allowed to escalate to the human because it transitions `.state` back to `plan`).
4. Never silently guess. Never improvise the missing detail.

This rule keeps long-running implementation runs from pinging the human every few minutes with questions that should have been resolved in spec/plan.

**The one exception: `STATUS: NEEDS_PRODUCT_DECISION`.** If the implementer surfaces a load-bearing product call (data custody/ownership, access control, an irreversible/destructive operation, billing/fees, data retention/privacy, a security trust boundary, external-service trust, or a breaking public-contract change), the loop IS allowed to interview the human directly during Stage 3 — because by definition the spec/plan was wrong to resolve it, and re-running the spec loop just to re-ask is wasteful. Follow the protocol in `status-handling.md §NEEDS_PRODUCT_DECISION` (label `state:needs-decision`, `[PRODUCT]`-prefixed open question, comment, exit). All other ambiguities still go through spec/plan revision, not the human inbox.

## Permission denials

Follow `permissions-handshake.md` instead — same shape, denial-specific template. Permission denials are treated as infra-level blockers, not product questions, so they pause regardless of `.state`.
