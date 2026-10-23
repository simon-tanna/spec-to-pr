# Spec Loop — Detailed Protocol

## Entry

Source is one of:

- A GitHub issue (`gh issue view $ISSUE`)
- A spec file path provided by the user
- An inline task description in the conversation

`source.md` holds that input byte-for-byte: `init-run.sh` writes it in interactive runs, and in CI the controller saves the issue body, spec file or inline task card unchanged.

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

**Pass 1 — structured review.** Dispatch `code-reviewer` with `prompts/decision-rules.md` prepended to `prompts/spec-reviewer.md`. Save the JSON it returns, unchanged, to `spec-review.md`; its schema (including `force_interview` and `product_decisions_flagged`, which the gate hook reads) is that prompt's §Output format.

**Pass 2 — validation.** Read and execute the bundled `references/validation/workflow.md` inline in the controller (see SKILL.md `## Spec & Plan Validation`), invoked as `<abs spec.md> --out <abs spec-validation.md>` plus the run's `--skill`/`--mcp`. `spec-review.md` stays Pass 1's file. The report's last line is the verdict: `Verdict: GO`, `Verdict: REVISE` or `Verdict: NO-GO`. `REVISE`/`NO-GO` feeds back into the next draft cycle exactly like a `critical`/`important` structured finding. Commit `spec-validation.md` via `scripts/git-sync.sh commit`.

## Interview

When the review fires the interview gate, run `interview-protocol.md`. In interactive mode, ask as soon as a question is obvious during the draft, without waiting for the review.

## Exit

Exit when the `spec` → `plan` gate in `stage-gates.md` holds. Then advance `.state` to `plan` and run `scripts/git-sync.sh commit "chore(loop): lock spec for #<issue>"`.

## Recurrence cap

This is the one recurrence rule for the spec and plan loops.

**Trigger:** the same `area` (in the plan loop, the same `task_id`, or `area` for plan-wide findings) appears in `critical` or `important` across two consecutive review iterations of one stage.

**On the trigger:**

1. Pipe a message naming the recurring area and its findings from both iterations into `"${AGENTIC_SKILL_DIR}/scripts/notify.sh" blocked "$ID" -`.
2. For a real GitHub issue, add label `state:blocked` via `scripts/gh-label.sh`.
3. Headless, unless this is a real issue under `github`: write `.agentic-loop/<id>/NEEDS_INPUT` naming the recurring area.
4. Run `scripts/git-sync.sh commit "chore(loop): blocked on recurring <area> for #<issue>"`; `.state` keeps the current stage.
5. Exit. Interactive: name the recurring area to the user and yield the turn. Headless: `exit 0` for a real issue under `github`, else `exit 78`.

## What a Good Spec Looks Like

- Requirements are traceable: every goal has at least one component that implements it and at least one test that verifies it.
- Architecture names the boundaries between units and the interface between each pair.
- Test strategy names the test types (unit/integration/e2e/property/fuzz) and which components each covers.
- Non-goals are listed. Anything ambiguous in the source that was deliberately scoped out lives here.
- Open questions is empty at lock time.
