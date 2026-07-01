# PR Body Template

The skill renders the PR body via `scripts/render-pr-body.sh <issue-id>` rather than by manually substituting placeholders — the script reads `tasks.json` + `spec.md` + `plan.md` and emits the body directly. Stage 4 step 3 pipes this into `gh pr create`:

```bash
bash scripts/render-pr-body.sh "$AGENTIC_ISSUE" \
  | gh pr create --base "$AGENTIC_BASE_REF" --title "<title>" --body-file -
```

The template below documents the shape the script produces. Treat it as a reference for the renderer, not as something to hand-edit per PR.

```markdown
## Summary

<One-paragraph summary of what this PR delivers, from the spec's Goals section>

Closes #<issue>.

## Spec & Plan

- Spec: `.agentic-loop/<id>/spec.md`
- Plan: `.agentic-loop/<id>/plan.md`

## Tasks Completed

<Generated from tasks.json — list each task with id, title, and commit SHA>

- [x] T1 — <title> (`<sha>`)
- [x] T2 — <title> (`<sha>`)
- ...

## Test Plan

<one line per gate `quality-gates.sh` actually resolved + ran, read from `./.agentic-resolved-gates`, e.g. `- test: ` + the command>
- Full gate: `bash .claude/skills/agentic-loop/scripts/quality-gates.sh`

## Risks & Notes

<From spec.md Risks section + anything surfaced in progress.log as a "concern">

## Agentic Loop Run

- Domains engaged: <comma-separated list from `tasks.json[].domain`>
- State files: `.agentic-loop/<issue>/`

🤖 Generated with [Claude Code](https://claude.com/claude-code) via the agentic-loop skill

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Rules

- Always `--base "$AGENTIC_BASE_REF"` (set by the workflow's pin step: config `base_ref`, then the issue's `Base branch` field, then `base:<ref>` label, then `main`). Never hardcode a base branch.
- Always link the source issue via `Closes #`.
- Never mark the PR as a draft unless the final review flagged `important` issues (then draft is correct).
- Do not include full spec/plan inline — link to the committed files.
