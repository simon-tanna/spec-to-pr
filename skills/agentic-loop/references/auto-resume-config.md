# Auto-Resume Configuration

Single source of truth for the CI auto-resume mechanism. Both the agentic-loop skill (`SKILL.md §Context Hygiene`) and the GitHub Actions workflow read these values. **Do not duplicate them anywhere else.**

## Source of truth

**Authoritative values live in this repo's GitHub Actions repository variables** (`Settings → Secrets and variables → Actions → Variables` tab). The workflow's job-level `if:` reads them via `vars.*`; the workflow's `Pin agentic-loop branch` step forwards `AGENTIC_RESUME_CAP` and `AGENTIC_RESUME_MARKER` into `$GITHUB_ENV` so the skill's bash snippets read them with safe fallbacks (`${AGENTIC_RESUME_CAP:-10}` etc.).

This markdown file is **documentation, not runtime config** — if you change a value, change it in repo variables. The values listed in the table below are the defaults the workflow falls back to when the repo variable is unset.

### Required repo variables

| Variable                | Default in workflow fallback |
| ----------------------- | ---------------------------- |
| `AGENTIC_BOT_LOGIN`     | `claude[bot]`                |
| `AGENTIC_BOT_USER_ID`   | `209825114`                  |
| `AGENTIC_RESUME_MARKER` | `AGENTIC-LOOP-AUTO-RESUME`   |
| `AGENTIC_RESUME_CAP`    | `10`                         |

Only `AGENTIC_RESUME_CAP` and `AGENTIC_RESUME_MARKER` have inline `|| 'default'` fallbacks in the workflow today. `AGENTIC_BOT_LOGIN` and `AGENTIC_BOT_USER_ID` are referenced from the job-level `if:` filter, where `||` fallback inside `vars.*` works but is harder to read — if the variables are unset the filter resolves to comparing against an empty string and auto-resume comments will not fire. **The two bot identity variables must be set.**

| Key              | Value                                   | Meaning                                                                                                                                                                                                                          |
| ---------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BOT_USER_LOGIN` | `claude[bot]`                           | Login the workflow filters on when matching auto-resume comments.                                                                                                                                                                |
| `BOT_USER_ID`    | `209825114`                             | GitHub user id for `claude[bot]`. Used by the workflow `if:` filter alongside the login because logins can be spoofed by issue creators.                                                                                         |
| `RESUME_CAP`     | `10`                                    | Maximum number of consecutive auto-resume attempts on a single feature branch before the loop pauses for human acknowledgement.                                                                                                  |
| `RESUME_MARKER`  | `AGENTIC-LOOP-AUTO-RESUME`              | The token embedded in an HTML comment inside the bot's eject comment. The workflow scans for this token (case-sensitive, anchored to an HTML comment line) when deciding whether to fire a fresh run on a `issue_comment` event. |
| `ATTEMPTS_FILE`  | `.agentic-loop/<issue>/resume-attempts` | Where the counter lives. Tracked in git so the cap survives across runs.                                                                                                                                                         |

## Marker format

The bot's comment MUST include exactly one HTML comment line matching the regex `<!-- AGENTIC-LOOP-AUTO-RESUME issue=#\d+ attempt=\d+/\d+ -->`. The workflow extracts `attempt` to display in its run name.

## Workflow `if:` filter

The workflow's auto-resume trigger fires only when ALL of:

1. `event.action == created` (new comment).
2. `event.comment.user.id == BOT_USER_ID` AND `event.comment.user.login == BOT_USER_LOGIN` (defence in depth — IDs are immutable, logins are easier to read).
3. `event.comment.body` contains `RESUME_MARKER`.

## Reset

The counter is reset to zero when the loop reaches Stage 4 and `gh pr create` succeeds (`SKILL.md §Stage 4` step 3). If the counter is at `RESUME_CAP` and the human types `@claude continue`, the workflow's separate `issue_comment` handler fires and clears the counter as part of resumption.

## Changing values

Bump `AGENTIC_RESUME_CAP` via repo variables (`Settings → Actions → Variables`). `AGENTIC_BOT_USER_ID` should only change if the underlying GitHub App is rotated — it is empirically `209825114` for the official `claude[bot]` App, confirmed via a real public comment. `AGENTIC_RESUME_MARKER` should only change in lock-step with this file's regex (a stale marker means the bot's own eject comment will fail the workflow `if:` and resumption will silently stop).

If you change the marker, also update any monitoring/regex in this file to match.
