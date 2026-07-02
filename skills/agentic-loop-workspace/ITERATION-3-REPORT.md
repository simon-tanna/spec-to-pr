# agentic-loop — Iteration 3 Report (post-eval improvements beyond triggering)

**Date:** 2026-07-02 · **Model:** claude-opus-4-8 · Builds on `REPORT.md` (iter 1) and
`ITERATION-2-REPORT.md` (iter 2).

Iteration 2 fixed the headline behavioural defect (eval-13 interview-gate bypass) and settled
triggering at 18/20. This iteration answers the follow-up question — *beyond triggering, what else do
the eval results reveal?* — by re-reading the produced artifacts and the skill internals with three
Explore agents. It found **two genuine defects** the gradings under-explained and **one by-design item
mis-graded as a failure**, and implements all three (plus deterministic backstops).

---

## What the evals actually showed (vs how they were first graded)

| Eval | First grading | Real finding |
|---|---|---|
| 6 | "missing Risks section (minor format gap)" | **§8 numbering collision.** `spec-planner.md`'s canonical list called §8 "Risks"; its own Step-0.5 prose + `spec-reviewer.md` check 12 called §8 "Resolved Decisions" (which had **no** numbered slot). The model wrote §8 Resolved Decisions and **silently dropped Risks**. Under other pressure it could drop Resolved Decisions instead — weakening the eval-13 interview gate that depends on that section. |
| 13 (iter-1) | FAIL: shipped under assumptions, no `spec-review.md` | Fixed in iter-2 by wording — but the **deterministic gate was asymmetric**: `agentic-loop-check-state-transition.sh` gated Stage 2→3 (`implement`) but let the Stage 1→2 (`plan`) transition through unconditionally, so no hook required `spec-review.md` to even exist. The wording caught it; the backstop had a hole. |
| 8 | FAIL: "TDD red-green not visible in git history" | **Mis-graded — by design.** `references/tdd.md:44` deliberately removed the git-order check because atomic "one task = one green commit" (bisectability) makes it unenforceable; it's replaced by a mandatory `TDD:` commit-body trace. Only real gap: that trace was **model-verified only**. |

**Dismissed as false positives** (verified, not skill behaviour): "state ID 1300 vs 13" is the eval
harness's deliberate run-id; the "unnumbered sections / missing per-task review shas in eval-13" were
from the *iteration-1 failed run*, already fixed in iteration-2.

---

## Fixes applied

### Improvement 1 — Resolve the §8 collision (fixes eval-6)
Promoted **Resolved Decisions** to a first-class numbered section. Final canonical order:
`… §7 Acceptance Criteria · §8 Resolved Decisions · §9 Open Questions · §10 Risks`.

- **Deviation from the approved plan (for the better):** the plan proposed Risks→§9, Open Questions→§10,
  which would have rewritten the load-bearing `§9 Open Questions` anchor at ~25 sites (SKILL.md, both
  prompts, plan-reviewer, plan-loop, evals.json) — the exact anchor the interview gate keys on. Instead
  I kept **Open Questions at §9** and moved only **Risks to §10**. Identical correctness, ~3 edits,
  **zero churn** on the interview anchor.
- Files: `prompts/spec-planner.md` (canonical list + header), `references/spec-loop.md` (exit
  criteria), `SKILL.md` (pipeline one-liner). The §8 section is now emitted even when empty ("None")
  so its absence can never be mistaken for a silent resolution.
- Static verification: `grep -rn '§[0-9]'` → no lingering "§8 Risks"; every `§8`=Resolved Decisions,
  `§9`=Open Questions, `§10`=Risks, all cross-references agree.

### Improvement 2 — Make the Stage 1→2 gate deterministic (hardens the eval-13 class)
- `setup/hooks/agentic-loop-check-state-transition.sh`: split `spec|plan)` — `spec)` stays a free
  pass; new **`plan)` branch** requires `spec.md` + `spec-review.md` present with JSON
  `verdict:"approved"` and `force_interview:false`, and `open-questions.md` empty/absent. Symmetric
  with the existing `implement)` gate. This deterministically stops the exact iter-1 eval-13 skip
  (which persisted no `spec-review.md`).
- Mandated `spec-review.md` be saved **verbatim as JSON** (SKILL.md step 6.1) so the hook can parse it
  (kills the eval-6 markdown drift too).
- Docs updated: `references/stage-gates.md` (gate table row + hook-enforced list), `SKILL.md`
  Interview-Discipline + Red-Flags now state the gate blocks **both** `plan` and `implement`.

### Improvement 3 — Deterministic TDD-trace hook (closes the eval-8 residual gap)
- New `setup/hooks/agentic-loop-check-tdd-trace.sh` (PreToolUse on `tasks.json`): for every task
  flipped to `status:"done"` with a **resolvable** `commit_sha`, confirms the commit diff contains a
  test path **and** the message body carries a `TDD:` line. Verifies **presence only** (never ordering
  — that would contradict the atomic-commit design). Empty/unresolvable shas pass, so it never blocks
  on git flakiness (only ever exits 0 or 2).
- Registered in `setup/settings.snippet.json`; added to `scripts/check-substrate.sh` `GATE_HOOKS`;
  documented in `references/tdd.md` (with an explicit "red→green is recorded via the TDD: trace, not
  auditable from git history — by design" note) and `references/stage-gates.md` (now "four hooks").
  `setup/SETUP.md` wording bumped three→four (its `agentic-loop-check-*.sh` glob already installs it).

---

## Verification

- **Hook unit tests** — extended `setup/hooks/__tests__/test-agentic-hooks.sh` from 11 → **22
  scenarios, all green**:
  - 5 new state-transition `plan`-gate cases (P1 no spec-review → block; P2 needs-changes → block;
    P3 approved → allow; P4 approved-but-open-questions → block; P5 `spec` free pass → allow).
  - 6 new TDD-trace cases against a throwaway git repo (test+TDD commit → allow; impl-only commit →
    block; empty sha → allow; unresolvable sha → allow; Edit fragment w/ bad sha → block; non-tasks.json
    write ignored → allow).
- **Static/lint** — `grep -rn '§[0-9]'` consistency confirmed; `jq empty` on the snippet + both
  updated gradings; `bash -n` clean on all four gate hooks.
- **Gradings re-scored** — `eval-06` evidence now records the root cause + fix (still `failed:true`
  pending a behavioural re-run to confirm both sections emit); `eval-08` re-graded **6/7 → 7/7** (the
  miscalibrated expectation corrected; real TDD: contract satisfied and now deterministically enforced).

### Behavioural re-runs (executed 2026-07-02, hooks registered, `iteration-3/`)
1. **eval-6** ✅ **PASS** — `spec.md` now emits `## 8. Resolved Decisions`, `## 9. Open Questions`,
   **and** `## 10. Risks`, correctly numbered. The collision is fixed; Risks is no longer dropped.
   (`.state=spec`, Stage-1-only, no code — scope respected.)
2. **eval-13** ✅ **PASS** — `.state=spec`, 45-line `open-questions.md`, `force_interview:true`, no
   `plan.md`/code. The in-situ **skip-probe blocked a premature `.state=plan` (exit 2)** — the `plan`
   gate is a working deterministic backstop.
3. **eval-8** ⚠️ **INCOMPLETE (budget), no regression** — advanced correctly through Stage 1 + Stage 2
   (spec-review approved, spec-validation GO, plan drafted → **rev2 revision** addressing validator
   blockers → plan-review approved → plan-validation GO) and entered `implement`. Ran out of the $15
   budget mid-Stage-3 before completing task T1, so **no `done` task was produced and the TDD-trace
   hook was not exercised end-to-end**. Notably, the **new `plan` gate did real work in situ**: it
   blocked premature spec→plan attempts 4× citing `verdict != approved` / `force_interview != false`,
   then allowed the transition once the spec-review was finalized — zero false-blocks. **Re-run at a
   higher budget ($30) to complete Stage 3+4 and confirm the TDD-trace hook on a real commit.** The
   hook logic itself is already proven by the 6 git-backed unit scenarios (T1–T6).

**Net:** 2/3 clean PASS; eval-8 budget-truncated but shows the new gates working and no regression.
The TDD-trace hook's end-to-end confirmation is the one remaining behavioural check.

---

## Net state after iteration 3
- **Structural:** the spec section schema is internally consistent for the first time (Risks can no
  longer be silently dropped; Resolved Decisions has a real slot).
- **Deterministic backstops:** Stage 1→2 now hard-gated symmetrically with Stage 2→3; the `TDD:` trace
  is structurally enforced, not model-only. Four gate hooks; 22/22 unit scenarios pass.
- **Docs:** SKILL.md, stage-gates.md, tdd.md, spec-loop.md, SETUP.md, settings.snippet.json,
  check-substrate.sh all consistent with the new behaviour.
- **Out of scope (unchanged):** trigger-description tuning (18/20, separate nudge-hook item) and the
  CI-mode evals (7, 10–12, 14–22) against a real GitHub repo + Actions.

## Artifacts (iteration 3)
- Skill diffs under `skills/agentic-loop/`: `prompts/spec-planner.md`, `references/spec-loop.md`,
  `references/stage-gates.md`, `references/tdd.md`, `SKILL.md`,
  `setup/hooks/agentic-loop-check-state-transition.sh`,
  `setup/hooks/agentic-loop-check-tdd-trace.sh` (new), `setup/hooks/__tests__/test-agentic-hooks.sh`,
  `setup/settings.snippet.json`, `setup/SETUP.md`, `scripts/check-substrate.sh`.
- Re-scored: `iteration-1/eval-06-.../grading.json`, `iteration-1/eval-08-.../grading.json`.
