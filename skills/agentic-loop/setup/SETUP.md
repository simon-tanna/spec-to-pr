# Installing the agentic-loop skill in a new repo

The skill itself is repo-agnostic, but it leans on a small **substrate** (config, hooks, a CI
workflow, and one sibling skill). This guide installs that substrate. The loop runs in two modes:

- **Interactive (local)** — needs only buckets 5 + 6 below. Drive it from a Claude Code session;
  it asks design questions via `AskUserQuestion`. Skip the CI/workflow buckets entirely.
- **CI (GitHub Actions)** — unattended runs triggered by labelled issues. Needs all six buckets.

Run `scripts/check-substrate.sh` at any time to see whether the deterministic gate hooks are
registered (they fire only when registered; otherwise the gates are model-enforced).

---

## 1. Workflow env contract (`AGENTIC_*` + `CLAUDE_MODEL`) — CI only

The workflow's "Pin agentic-loop branch" step computes and exports these into `$GITHUB_ENV`; the
skill reads them. Use `setup/agentic-loop.yml` as the starting template.

| Variable                 | Set by                | Purpose                                                              |
| ------------------------ | --------------------- | ------------------------------------------------------------------- |
| `AGENTIC_ISSUE`          | pin step              | issue number the run owns                                           |
| `AGENTIC_BRANCH`         | pin step              | deterministic `feat/<issue>-<slug>` branch                          |
| `AGENTIC_SLUG`           | pin step              | slug derived from the issue title                                   |
| `AGENTIC_BASE_REF`       | pin step              | base ref (config `base_ref` → issue `Base branch:` → `base:` label → `main`) |
| `AGENTIC_AUTHOR`         | pin step              | issue author (gh-comment.sh @-mentions them)                        |
| `AGENTIC_RUN_STARTED_AT` | pin step              | unix epoch; wall-clock budget for context hygiene                   |
| `CLAUDE_MODEL`           | workflow `env:`       | the model id; **must equal** the `--model` passed to Claude. If unset, eject thresholds default to Opus and a smaller-model run can overflow context. |

## 2. Repo variables (bot identity + resume cap) — CI only

These are GitHub Actions **repository variables** (`Settings → Secrets and variables → Actions →
Variables`), consumed by the workflow `if:` filter via `vars.*` — they are **not** skill env vars.
See `references/auto-resume-config.md` (the single source of truth).

| Repo variable           | Default        | Notes                                                              |
| ----------------------- | -------------- | ------------------------------------------------------------------ |
| `AGENTIC_BOT_LOGIN`     | `claude[bot]`  | login the auto-resume filter matches (**must be set**)             |
| `AGENTIC_BOT_USER_ID`   | `209825114`    | immutable id for `claude[bot]` (**must be set**; logins spoofable) |
| `AGENTIC_RESUME_MARKER` | `AGENTIC-LOOP-AUTO-RESUME` | token in the bot's eject comment                       |
| `AGENTIC_RESUME_CAP`    | `10`           | max consecutive auto-resumes before pausing for a human           |

Also set the `ANTHROPIC_API_KEY` **secret**.

## 3. Hooks + registration + probe — both modes (recommended)

The three gate hooks make the stage gates *deterministic* (the harness blocks the bad tool call).
Without registration the gates still hold, but only because the controller self-enforces them.

1. Copy the gate hooks from `setup/hooks/` to `.claude/hooks/` (and keep the skill's context hooks
   in `.claude/skills/agentic-loop/scripts/`). Make them executable (`chmod +x`).
2. Merge `setup/settings.snippet.json` into `.claude/settings.json` (create it if absent; deep-merge
   the `hooks` arrays if it exists). This registers: the 3 gate hooks (PreToolUse), the context-check
   (PostToolUse), and the precompact flush (PreCompact).
3. Run `scripts/check-substrate.sh` — it must report all three gate hooks registered.

**Opt-in / repo-policy hooks (NOT in the snippet):** `block-ts-violations.sh` (language-specific —
register only on TS repos), `force-agentic-loop.sh` (CI-only; forces the skill on a pinned branch),
and the `block-env-reads.sh` / `block-destructive-git.sh` / `block-secret-exfil.sh` security hooks
(good defaults, but your call).

## 4. `validating-specs` skill dependency — both modes

The loop invokes the `validating-specs` skill (via the Skill tool) at spec-lock and plan-lock. It is
a **hard dependency** — if absent, the validation gate cannot run and the loop treats it as a
`BLOCKED_PERMISSION`-class setup failure. Install it alongside this skill.

## 5. Optional `.agentic-loop.config.json` — both modes

Repo root. Everything in it is optional; absent ⇒ auto-detect defaults. Declares the base ref,
quality-gate commands, agent roster (planner/reviewer/specialists), and extra `risk_categories`.
See `references/config.md` for the full shape and the auto-detect defaults. The most common reason
to add it: your quality gates aren't standard `package.json` scripts, or you want named specialists.

## 6. Quality gates — both modes

`scripts/quality-gates.sh` auto-detects the package manager and runs the `test`/`lint`/`typecheck`/
`build` scripts that exist (or `cargo`/`go`/`pytest` for non-JS repos). If it finds **no** runnable
gate it refuses to proceed (so an unverifiable repo never ships silently) — either give it commands
via `.agentic-loop.config.json` `quality_gates`, or set `"quality_gates": {}` to opt out explicitly.
It records the resolved set to `./.agentic-resolved-gates` (gitignored) for the PR body.

---

## Minimal local-only setup

For interactive runs with no CI: install `validating-specs` (bucket 4), optionally add
`.agentic-loop.config.json` (bucket 5), ensure your quality gates resolve (bucket 6), and optionally
register the hooks (bucket 3) for deterministic gates. Then, in a Claude Code session, point the
skill at a spec/issue/task-card and let it drive.
