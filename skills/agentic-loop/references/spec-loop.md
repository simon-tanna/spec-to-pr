# Spec Loop — Detailed Protocol

## Entry

Source is one of:

- A GitHub issue (`gh issue view $ISSUE`)
- A spec file path provided by the user
- An inline task description in the conversation

Save the raw content verbatim to `.agentic-loop/<id>/source.md`. Do not interpret it yet.

**`source.md` shape:**

- UTF-8 markdown, no other format.
- Soft cap 64KB. If the source is larger, truncate the body and append `\n\n[…truncated — see <permalink to the full source>]` so the controller can still resolve the original.
- For GitHub issues, include the issue title as an H1 and the body verbatim below. Do not include comment threads — those are fetched separately when an open question is resolved.
- For spec files, prepend a `Source: <path>` line; the body is the file verbatim.
- For inline task descriptions, prepend `Source: inline conversation @ <ISO timestamp>` then the verbatim user text.

## Branch

The workflow's "Pin agentic-loop branch" step has already checked out `feat/<issue>-<slug>` and exported `$AGENTIC_BRANCH`. Verify HEAD matches; never run the loop on `main`. Do not call `git checkout -b` from inside the skill — the workflow owns branch creation.

## Draft Cycle

Each iteration:

1. Call the configured planner (`agents.planner`) with `prompts/spec-planner.md`, passing:
   - `source.md`
   - Previous `spec.md` (if any)
   - Previous `spec-review.md` (if any)
   - Answers from `open-questions.md` (if any)
2. The planner returns a fresh `spec.md`. Overwrite the file.
3. Run `scripts/git-sync.sh commit "chore(loop): draft spec v<N> for #<issue>"`.

## Review — two passes

Both passes run every iteration. The structured pass drives the interview gate; the validation pass is a deeper pressure-test. Neither replaces the other.

**Pass 1 — structured review.** Dispatch `code-reviewer` with `prompts/spec-reviewer.md`. Output is structured JSON saved to `spec-review.md`:

```json
{
  "verdict": "approved|needs-changes",
  "critical": [{"area": "...", "issue": "...", "fix": "..."}],
  "important": [...],
  "minor": [...],
  "open_questions": ["..."]
}
```

**Pass 2 — validation.** Invoke the `spec-to-pr:validating-specs` skill via the Skill tool from the controller (inline in the main session — never as a subagent; see SKILL.md `## Spec & Plan Validation` for the full dispatch contract). Pass the explicit `spec.md` path and direct its merged report to `spec-validation.md` (NOT `spec-review.md`, which Pass 1 owns). It returns one `GO | REVISE | NO-GO` verdict. A `REVISE`/`NO-GO` verdict feeds back into the next draft cycle exactly like a `critical`/`important` structured finding. Commit `spec-validation.md` via `scripts/git-sync.sh commit`.

## Interview

If the review surfaces `open_questions` that the spec cannot resolve without human input, go to the CI-aware interview handshake (see `ci-mode.md`). In interactive mode, ask via `AskUserQuestion` immediately — do not wait for the review to accumulate questions if they are obvious during the draft.

## Loop Exit

Exit criteria (all must hold):

- `spec-review.md` `verdict` = `approved`
- `critical` empty
- `important` empty
- `spec-validation.md` verdict is `GO` (a `REVISE`/`NO-GO` blocks the exit exactly like an `important` finding)
- `open_questions` empty
- Spec has: Context, Goals, Non-goals, Architecture, Components, Test Strategy, Risks, and at least one acceptance criterion per goal

On exit, advance `.state` to `plan`, then run `scripts/git-sync.sh commit "chore(loop): lock spec for #<issue>"`.

## Recurring-issue Escalation

Escalate to the human when the same `area` (or `task_id` for plan-loop) appears in `critical` or `important` across two consecutive iterations. This is the single deterministic recurrence trigger — volume heuristics ("> 5 important findings", "> 3 unrelated bugs") were removed because no counter state existed to enforce them and they encouraged vibes-based escalation.

On the trigger:

- Interactive: ask the user explicitly, naming the recurring area.
- CI: post a comment on the issue, set label `state:blocked` (or `state:needs-decision` if the recurring finding was PRODUCT-class), and exit 0.

Do NOT silently keep iterating.

## What a Good Spec Looks Like

- Requirements are traceable: every goal has at least one component that implements it and at least one test that verifies it.
- Architecture names the boundaries between units and the interface between each pair.
- Test strategy names the test types (unit/integration/e2e/property/fuzz) and which components each covers.
- Non-goals are listed. Anything ambiguous in the source that was deliberately scoped out lives here.
- Open questions is empty at lock time.
