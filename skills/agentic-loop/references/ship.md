# Ship (Stage 4)

**Goal:** a PR opened (or, without a forge, a committed PR body and `SHIP_READY` sentinel) on a fully reviewed, green branch.

**Entry:** `.state == implement` and every task in `tasks.json` is `done` with both `spec_review_sha` and `quality_review_sha` populated.

## Steps

The order is fixed: final review → quality gates → PR → label → completion marker. When a step fails, stop there.

1. **Final review.** Dispatch the configured reviewer with the bundled review role (Claude tier: `model: "opus"`) and `prompts/final-review.md` against the full branch diff versus the base ref: `git diff "origin/${AGENTIC_BASE_REF:-main}...HEAD"`. Use the `origin/` prefix, because local branches do not exist on the Actions runner; in interactive mode the local-branch form also works. A `needs-changes` verdict sends every critical and important finding back to Stage 3 as a new fix task (`execution-loop.md`).
2. **Pre-PR gates.** Re-run `${AGENTIC_SKILL_DIR}/scripts/quality-gates.sh` on the full branch and `check-gates.sh pr-ready --run-dir "$RUN_DIR"`. Both must succeed before PR creation or `SHIP_READY` publication.
3. **Open PR.** Render the body deterministically with `${AGENTIC_SKILL_DIR}/scripts/render-pr-body.sh "$AGENTIC_ISSUE"`; it reads `tasks.json`, `spec.md` and `plan.md`, so the body always matches committed state. Then, by adapter:
   - **`IO_ADAPTER=github`:** pipe it into `gh pr create --base "$AGENTIC_BASE_REF" --title "<title>" --body-file -`. See `pr-template.md`.
   - **Otherwise (`file`/`webhook`/`command`):** write the rendered body to `.agentic-loop/<id>/PR_BODY.md`, announce it via `notify.sh pr "$ID" .agentic-loop/<id>/PR_BODY.md`, and drop a `.agentic-loop/<id>/SHIP_READY` sentinel. Opening the PR needs a git remote and forge credentials the sandbox may not have; that is the host harness's job (see `ci-mode.md` and SETUP.md "out of scope").
4. **Label.** For a real GitHub issue only, set `state:in-pr` and remove `state:implementing`.
5. **Reset auto-resume counter.** Run `rm -f ".agentic-loop/${AGENTIC_ISSUE}/resume-attempts"`, then `${AGENTIC_SKILL_DIR}/scripts/git-sync.sh commit "chore(loop): reset resume-attempts on PR open for #${AGENTIC_ISSUE}"`, so a future re-run on the same issue does not inherit the cap. See `auto-resume-config.md`.
6. **Verify, then emit completion.**
   - Under `IO_ADAPTER=github`, run `gh pr list --head "$AGENTIC_BRANCH" --state open --json number --jq 'length'` and confirm it prints `≥ 1`. If `gh pr create` returned non-zero or the count is zero, escalate via `${AGENTIC_SKILL_DIR}/scripts/notify.sh blocked "$ID" -` and exit non-zero, so the workflow's failure-comment branch fires; COMPLETE is withheld.
   - Under other adapters, confirm `.agentic-loop/<id>/PR_BODY.md` and `SHIP_READY` were written and committed.
   - Then output `<loop-state>COMPLETE</loop-state>`, followed by the PR URL (or the `PR_BODY.md` path) and a one-paragraph summary.

## Exit

Exit when the `implement` → PR open gate in `stage-gates.md` holds and step 6 emitted COMPLETE. `.state` stays `implement` after `gh pr create` succeeds; the merge pipeline owns `state:done`.
