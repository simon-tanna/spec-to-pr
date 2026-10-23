# CI Mode (GitHub Actions)

The agentic loop is designed to survive across GitHub Action invocations. A single CI run rarely completes the whole pipeline — it may pause for a human answer, finish one stage, exhaust `--max-turns`, or hit a quality gate failure. The loop resumes on the next trigger because all durable state lives in committed-and-pushed files on a deterministic feature branch.

## Deterministic Branch Contract

`claude-code-action@v1` defaults to creating a fresh timestamped branch on every `issues`-triggered run. That breaks resumption — state files committed on run N's branch are invisible to run N+1, which lands on a new branch.

The workflow's "Pin agentic-loop branch" step (in `.github/workflows/claude.yml`) runs **before** the action and pins HEAD to `feat/<issue>-<slug>`. When the action then starts, that is its "branch where invoked", so its commit/push tooling targets the resumable branch. The skill must:

- Read `$AGENTIC_BRANCH`, `$AGENTIC_ISSUE`, `$AGENTIC_SLUG` from env at start, and verify HEAD is `$AGENTIC_BRANCH` before the first commit.
- Leave branch creation to the workflow: work on the pinned branch as checked out.
- Use `scripts/git-sync.sh commit "..."` for every state mutation. The script asserts HEAD is not `main` and not detached, commits, then pushes to origin.

## Detection

Interactivity is resolved by `scripts/lib-mode.sh` (the single source of truth) into `interactive` | `headless`. GitHub Actions is one headless harness; `AGENTIC_HEADLESS=1` / `AGENTIC_MODE=headless` opt any other harness in. See SKILL.md §Operating Modes for the two-axis model (interactivity + `IO_ADAPTER`).

```bash
MODE="$(bash "${AGENTIC_SKILL_DIR}/scripts/lib-mode.sh")"  # interactive | headless
# GitHub Actions resolves to MODE=headless, IO_ADAPTER=github — the pair this
# document historically called "CI mode". Its behaviour is unchanged.
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

The interview protocol (gate signals, the open-questions file, adapter-aware exit, resume parsing) is `interview-protocol.md`; permission denials follow `permissions-handshake.md`. The GitHub transport: `notify.sh questions` posts the questions as an issue comment, the run exits `0`, and the next `issue_comment` from a human on the same issue resumes it.

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

Eject protocol and snippet: `context-hygiene.md`. Thresholds: `scripts/postooluse-context-check.sh`. Auto-resume marker, workflow guard and cap: `auto-resume-config.md`. A human `@claude stop` comment halts auto-resume.

## Safety

- Never run `git push --force` from the loop. If a rebase is needed, push to a new branch `feat/<id>-<slug>-retry` and open a new PR; leave the old one for humans to close.
- Never merge from the loop. `gh pr merge` is forbidden in skill code.
- Never skip CI — if `scripts/quality-gates.sh` fails, the loop does not commit.
- Secrets come from workflow `env:` — never read from the repo.
