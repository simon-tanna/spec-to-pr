# Spec Loop (Stage 1)

**Goal:** a spec that a specialist can plan from without follow-up questions.

**Entry:** no `.agentic-loop/<id>/.state` file (fresh start), or `.state == spec` (resuming after a pause or a human reply). Every invocation runs step 1, whatever `.state` holds: step 1.5 sends a resumed run to the stage file for its `.state`.

## Source

Source is one of:

- A GitHub issue (`gh issue view $ISSUE`)
- A spec file path provided by the user
- An inline task description in the conversation

`source.md` holds that input byte-for-byte: `init-run.sh` writes it in interactive runs, and in CI the controller saves the issue body, spec file or inline task card unchanged.

## Steps

1. **Ingest.** Run these sub-steps in order.
   1. **Identify the run.**
      - Interactive: read `interactive-init.md` and run `scripts/init-run.sh` with the source file, or resume using saved metadata. For an inline request, snapshot it to a temporary file first and pass `--title inline-spec`, unless the user supplied a title. Honor the helper's preflight, identity, branch-collision and resume rules.
      - Existing Claude CI: read the supplied `AGENTIC_*` context and verify HEAD is on `$AGENTIC_BRANCH`. Never run the interactive helper to reset a CI-prepared branch.
      - Map the returned run ID, branch and base into `ID`, `AGENTIC_ISSUE` (the legacy helper run-ID argument), `AGENTIC_BRANCH` and `AGENTIC_BASE_REF` for each helper invocation. Keep the optional real issue number separately, for issue-only operations: a run ID is not necessarily a GitHub issue. `notify.sh` uses the metadata's real issue for GitHub comments and falls back to file notifications for issue-less runs, without changing PR adapter selection.
      - When the helper raises a blocking question, preserve `open-questions.md` and `NEEDS_INPUT` before checkpointing; ask interactively and wait or yield for the answer.

      Done when `ID`, `AGENTIC_BRANCH` and `AGENTIC_BASE_REF` are known and `git rev-parse --abbrev-ref HEAD` prints `$AGENTIC_BRANCH`.
   2. **Parse args.** Skip to 1.3 when this is a resume: `run-requirements.json` exists, the helper returned `resumed:true`, or `.state` exists. Otherwise parse `[--skill a,b] [--mcp x,y] [--subagent t1,t2]` once, from the `$ARGUMENTS` block in SKILL.md §Invocation arguments (Claude) or from the actual invocation and request (other harnesses). An empty or literal placeholder is not data and does not erase flags the user supplied. Done when you hold the three flag lists, each possibly empty.
   3. **Resolve requirements.**
      - Resume: reload `run-requirements.json` unchanged, even when `.state` is absent; the persisted file is the immutable run config, and new invocation flags are ignored. If the helper's `resumed:true` or an existing `.state` indicates a prior run but `run-requirements.json` is missing, stop for explicit ingest recovery rather than building a new configuration from the new request.
      - Fresh start: read `.agentic-loop.config.json` if present (base ref, quality gates, agent roster, risk categories; see `config.md`; absent ⇒ auto-detect defaults). Build `{skills, mcps, specialists}` per `invocation-args.md`: skills and mcps are `dedup(flags ∪ config.required)`; `specialists` is a validated `--subagent` roster when present, **fully replacing** `agents.specialists`, else config, else the single default `general-purpose`. Validate every `--subagent` name (resolvable and code-capable, per that reference) before use, and surface a failure through the interactive question interface or `notify.sh blocked`, never through the interview-exit path. Write `.agentic-loop/<id>/run-requirements.json`.

      Done when `jq -e 'has("skills") and has("mcps") and has("specialists")' .agentic-loop/<id>/run-requirements.json` exits 0.
   4. **Preflight.** Run `git status` and `command -v jq`; run `gh auth status` too when the resolved I/O adapter is `github`. On any failure, follow `BLOCKED_PERMISSION` in `status-handling.md` and do no stage work. Quality gates resolve per repo through `scripts/quality-gates.sh` (config or auto-detect), so no single package manager is required. Done when every probe exits 0.
   5. **Banner and resume check.** In headless mode, post **exactly one** banner via `"${AGENTIC_SKILL_DIR}/scripts/notify.sh" banner "$ID" -` before any subagent dispatch, so the human sees where the run started even if it later exhausts turns silently. Under `IO_ADAPTER=github`, include the branch link `https://github.com/${GITHUB_REPOSITORY}/tree/${AGENTIC_BRANCH}`; other adapters omit it, since there may be no GitHub remote.

      ```
      🚀 Starting agentic-loop for #<issue>
      Branch: [<branch>](<branch-url>)
      Stage: spec
      ```

      On a resume (`.state` exists), read `.state` and the current task from `tasks.json`, post the resume flavour instead, then follow the SKILL.md router to the stage file for `.state`:

      ```
      🔄 Resuming agentic-loop for #<issue>
      Branch: [<branch>](<branch-url>)
      Stage: <state>
      Current task: <id-or-none>
      ```

      Done when the banner is posted (headless) and you have either routed to another stage file or confirmed a fresh start.
   6. **Ingest commit (fresh start).** Interactive runs already hold the helper's `source.md`. In CI, read the source (issue body via `gh issue view $ISSUE`, the spec file, or the inline task card) and save it raw to `.agentic-loop/<id>/source.md`. Check the `spec` transition with the shared state check (SKILL.md §Shared checks before mutations), write `.state = spec`, then run `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "chore(loop): ingest source + run config for #<issue>"`. This one commit captures `source.md`, `run-context.json`, `run-requirements.json` and `.state`. Done when `git log -1 --format=%s` prints that message.
2. **Set label.** For a real GitHub issue under the GitHub adapter, set `state:planning` via `${AGENTIC_SKILL_DIR}/scripts/gh-label.sh`. Skip issue-only labels and comments for file and inline runs; never pass a synthetic run ID to a GitHub issue operation.
3. **Draft.** Dispatch a fresh configured planner child (`agents.planner`) with `prompts/decision-rules.md` prepended to `prompts/spec-planner.md` and `model: "opus"`, passing `source.md`, the previous `spec.md`, the previous `spec-review.md` and answers from `open-questions.md` (each if present). The planner returns a draft `spec.md`: Context · Goals · Non-goals · Architecture · Components · Test Strategy · Acceptance Criteria · Resolved Decisions · Open Questions · Risks. Overwrite `spec.md` and run `scripts/git-sync.sh commit "chore(loop): draft spec v<N> for #<issue>"`.
   - When the draft has a `## Research Needed` section, **the controller** dispatches the relevant specialist from `run-requirements.json.specialists`, prepending the REQUIRED TOOLING block built from `run-requirements.json` (`invocation-args.md`) so research honours the run's required skills and MCPs. Pass the findings into the next draft. The planner never dispatches specialists itself.
4. **Interview.** When the draft's Open Questions section is non-empty, or the latest `spec-review.md` fires the interview gate, run `interview-protocol.md`. In interactive mode, ask as soon as a question is obvious during the draft, without waiting for the review. Done when `open-questions.md` is closed, or the run has paused per that protocol.
5. **Merge answers.** Fold each answer into `spec.md`, then close `open-questions.md` per `interview-protocol.md` §Open-questions file.
6. **Review — two passes.** Both run every iteration; neither replaces the other.
   1. **Structured review (drives the interview gate).** Dispatch a fresh configured reviewer carrying the bundled role, with `prompts/decision-rules.md` prepended to `prompts/spec-reviewer.md` and `model: "sonnet"`. Save the JSON it returns to `spec-review.md` **verbatim**, never reformatted to prose or markdown: its schema is that prompt's §Output format, and the `spec` → `plan` gate hook parses `verdict`, `force_interview` and `product_decisions_flagged` out of this file. This pass is the source of the interview machinery; it runs every iteration.
   2. **Validation pass (deeper pressure-test).** Run the bundled `references/validation/workflow.md` inline in this controller (SKILL.md §Spec & Plan Validation), invoked as `<abs spec.md> --out <abs .agentic-loop/<id>/spec-validation.md>` plus the run's `--skill`/`--mcp` from `run-requirements.json` (never `--subagent`). `spec-review.md` stays the structured pass's file. The report's last line is the verdict: `Verdict: GO`, `Verdict: REVISE` or `Verdict: NO-GO`. Then run `scripts/git-sync.sh commit "chore(loop): spec validation for #<issue>"`.
7. **Loop.** While `spec-review.md` has any `critical` or `important` finding, or the `spec-validation.md` verdict is `REVISE` or `NO-GO`: check the eject flag (SKILL.md §Context hygiene), then return to step 3 with both the structured findings and the validation Blockers/Majors as planner input. Apply §Recurrence cap when it triggers.
8. **Exit** per §Exit.

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

## Exit

Exit when the `spec` → `plan` gate in `stage-gates.md` holds. Run the shared state check for `plan`, advance `.state` to `plan`, and run `scripts/git-sync.sh commit "chore(loop): lock spec for #<issue>"`. Continue with `plan-loop.md`.
