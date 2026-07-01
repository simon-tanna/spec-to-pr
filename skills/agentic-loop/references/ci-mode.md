# CI Mode (GitHub Actions)

The agentic loop is designed to survive across GitHub Action invocations. A single CI run rarely completes the whole pipeline — it may pause for a human answer, finish one stage, exhaust `--max-turns`, or hit a quality gate failure. The loop resumes on the next trigger because all durable state lives in committed-and-pushed files on a deterministic feature branch.

## Deterministic Branch Contract

`claude-code-action@v1` defaults to creating a fresh timestamped branch on every `issues`-triggered run. That breaks resumption — state files committed on run N's branch are invisible to run N+1, which lands on a new branch.

The workflow's "Pin agentic-loop branch" step (in `.github/workflows/claude.yml`) runs **before** the action and pins HEAD to `feat/<issue>-<slug>`. When the action then starts, that is its "branch where invoked", so its commit/push tooling targets the resumable branch. The skill must:

- Read `$AGENTIC_BRANCH`, `$AGENTIC_ISSUE`, `$AGENTIC_SLUG` from env at start.
- Never run `git checkout -b` itself.
- Use `scripts/git-sync.sh commit "..."` for every state mutation. The script asserts HEAD is not `main` and not detached, commits, then pushes to origin.

## Detection

```bash
[ "${GITHUB_ACTIONS:-}" = "true" ] && MODE=ci || MODE=interactive
```

## Environment

Available in a standard `issue_comment` / `issues` / `workflow_dispatch` event:

- `GITHUB_REPOSITORY` — `owner/repo`
- `GITHUB_EVENT_PATH` — JSON payload of the triggering event
- `GITHUB_ACTOR` — the user who triggered it
- `GITHUB_RUN_ID` — current run

Parse the issue number:

```bash
ISSUE=$(jq -r '.issue.number // .pull_request.number // empty' "$GITHUB_EVENT_PATH")
```

If no issue number is available, the workflow was misconfigured — exit non-zero with a message, do not guess.

## Interview Handshake

In interactive mode, `AskUserQuestion` blocks. In CI that is not possible. Protocol below covers Stage 1 spec questions; for ANY stage producing an open question, see SKILL.md §Mid-Stage Question Protocol — same shape, stage-agnostic. For permission denials see `references/permissions-handshake.md`.

**The interview gate fires when ANY of the following is true on the latest `spec-review.md`:**

- `force_interview === true`
- `open_questions[]` is non-empty
- `product_decisions_flagged[]` contains any item with `authorised_by_source: false`

An empty `open_questions[]` does NOT mean the spec is locked. The gate checks all three signals. Only when `force_interview === false` AND `open_questions[]` is empty AND every `product_decisions_flagged[]` entry has `authorised_by_source: true` is the spec cleared to advance.

**When the gate fires:**

1. Collect questions from BOTH `open_questions[]` AND from `product_decisions_flagged[where !authorised_by_source]`. Frame each unauthorised product decision as a Confirm question: "Confirm: <decision>? Suggested default (if any): <X>".
2. Write them to `.agentic-loop/<id>/open-questions.md` as a numbered list.
3. Post a single issue comment via `scripts/gh-comment.sh` with the questions and a reply format (one answer per numbered line, or inline under each heading).
4. **Write `.state` = `spec` to `.agentic-loop/<id>/.state`.** This is mandatory even on a fresh-start run where `.state` did not previously exist — the file must be on disk so the next CI trigger knows to resume at the spec stage rather than re-ingest from scratch.
5. Run `scripts/git-sync.sh commit "chore(loop): pause for open questions on #<issue>"`. This commits and pushes `spec.md` draft + `open-questions.md` + `.state`.
6. Exit 0 from the workflow. The loop halts.

On the next `issue_comment` trigger:

1. Check whether the comment is from a human (not the bot) and on the same issue.
2. Parse answers against the stored `open-questions.md`.
3. Resume the spec loop with the answers folded into the next draft.
4. Delete `open-questions.md`.

If the comment cannot be parsed cleanly, post a follow-up comment asking for the expected format and exit.

## Label Management

Use `scripts/gh-label.sh <add|remove> <issue-number> <label>`. The script is idempotent. Never modify labels directly with `gh api` from the main skill — go through the script so the state machine stays auditable.

## Commit Conventions Inside the Loop

All commits go through `scripts/git-sync.sh commit "..."` so they are pushed atomically. Each stage transition is its own commit so the history tells the loop's story:

- `chore(loop): start spec loop for #<issue>`
- `chore(loop): draft spec v<N> for #<issue>`
- `chore(loop): lock spec for #<issue>`
- `chore(loop): draft plan v<N> for #<issue>`
- `chore(loop): lock plan for #<issue>`
- `<type>(<scope>): <task title> [#<issue>]` for task commits
- `chore(loop): finish <task-id> [#<issue>]` for state-only commits after a task
- `chore(loop): final review pass for #<issue>`

## Max-Turns Exhaustion

`--max-turns` exhaustion is not a graceful exit — the agent stops mid-thought, possibly between two tool calls. Mitigations:

1. **Commit eagerly.** Every state mutation goes through `scripts/git-sync.sh commit` immediately. Never accumulate multiple unsaved mutations.
2. **Checkpoint at every pause point.** Use `scripts/git-sync.sh checkpoint "<reason>"` before any deliberate exit and at every stage boundary. Empty-diff tolerant.
3. **Prefer pause to dispatch when budget is low.** If the remaining turn budget cannot plausibly complete the next subagent dispatch + review, `checkpoint` and exit cleanly so the next trigger has a sane resume point.

On the next trigger, `git-sync.sh` will find the deterministic branch already on origin, the skill will read `.state` and `tasks.json`, and the Resume Banner will tell the human exactly where it left off.

## PR Creation in CI

After the resolved quality gates pass on the full branch, use `gh pr create --base "$AGENTIC_BASE_REF" --head <branch>`. The base ref comes from the workflow's pin step (config `base_ref`, then issue body field `Base branch:`, then `base:<ref>` label, then `main`). If a PR already exists for the branch, skip creation; new commits are already on origin via `scripts/git-sync.sh commit` and the PR will pick them up automatically. `gh pr view` returns zero when a PR exists.

## Context Hygiene

The `PostToolUse` context-check hook fires on every tool call and performs a token-estimate check every 15 invocations. When the estimated usage exceeds the threshold it drops `.agentic-loop/eject-flag`. The skill polls this flag at per-task checkpoints and at the top of each review-loop iteration, then exits cleanly. A fresh CI run picks up from the committed branch state.

**Thresholds (model-specific):**

| Model                            | Threshold   | Rationale                                       |
| -------------------------------- | ----------- | ----------------------------------------------- |
| `claude-opus-4-7` (and any opus) | 400k tokens | Near full window; coherence degrades above this |
| `claude-sonnet-*`                | 160k tokens | 80% of ~200k sonnet window                      |

**Feature flag:** `AGENTIC_LOOP_CONTEXT_HYGIENE=0` in workflow `env:` disables the eject check in the hook script. Remove or set to `1` to enable (default: enabled in CI).

**`CLAUDE_MODEL` env var** is stamped by the workflow's "Run Claude Code" step so the hook can read it. If absent the hook defaults to opus thresholds.

**`PreCompact` safety net:** `scripts/precompact-flush.sh` runs `git-sync.sh checkpoint` before any compaction (auto or manual), independent of the 15-turn heuristic. The "state in git before reset" invariant is thus doubly enforced.

**Turn counter persistence:** the counter lives at `.agentic-loop/turn-counter`. It is a plain integer file, not committed to git (it resets on each fresh CI run, which is correct — we want the 15-turn check relative to the current session, not across runs).

### Auto-resume contract

After a clean eject the skill posts a comment containing an HTML-comment marker. The workflow's `if:` watches for this marker and fires a fresh run automatically — no human ping required.

**Marker format** (appended to the eject comment body):

```
<!-- AGENTIC-LOOP-AUTO-RESUME issue=#<n> attempt=<k>/10 -->
```

**Workflow guard** (`.github/workflows/claude.yml`): the auto-resume `if:` branch requires:

- `github.event_name == 'issue_comment'`
- `github.event.comment.user.login == 'claude[bot]'`
- `github.event.comment.user.id == 209825114` (numeric id; forgery-proof)
- `contains(github.event.comment.body, '<!-- AGENTIC-LOOP-AUTO-RESUME ')`

Only `claude[bot]` posting from this GitHub App identity can satisfy all four. An attacker pasting the marker in their own comment fails the id check.

**Cap:** `.agentic-loop/<issue>/resume-attempts` (committed to branch) tracks consecutive auto-resumes. The skill increments this before posting. At attempt > 10 the marker is suppressed, the comment instead pings `@AGENTIC_AUTHOR`, and the loop waits for a human `@claude continue`.

**Human override:** any `@claude …` comment from a non-bot user fires the existing human-trigger branch and the skill picks up the instruction on the next run. `@claude stop` is the conventional halt signal.

## Safety

- Never run `git push --force` from the loop. If a rebase is needed, push to a new branch `feat/<id>-<slug>-retry` and open a new PR; leave the old one for humans to close.
- Never merge from the loop. `gh pr merge` is forbidden in skill code.
- Never skip CI — if `scripts/quality-gates.sh` fails, the loop does not commit.
- Secrets come from workflow `env:` — never read from the repo.
