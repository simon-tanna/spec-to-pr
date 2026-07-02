# agentic-loop — Iteration 2 Report (fixes + confirmation)

**Date:** 2026-07-01 · **Model:** claude-opus-4-8 · Builds on iteration 1 (`REPORT.md`).

Applied the three prioritized fixes, then re-measured. Headline: **the behavioural defect (eval 13)
is fixed and confirmed; the description change was trimmed to only its net-positive part.**

---

## Fixes applied to the skill

| # | Fix | File(s) | Kept? |
|---|---|---|---|
| 1 | Headless "notify-and-exit, never decide-and-proceed" rule; names the "conservative assumption / confirm-before-merge" anti-pattern; load-bearing decisions must exit without shipping | `SKILL.md` (Interview Discipline + Red Flags), `references/interview-protocol.md` | ✅ **kept** |
| 2 | Drop `"ralph this"` trigger (loses 3/3 to the installed `ralph-loop` plugin) | `SKILL.md` description | ✅ **kept** |
| 3 | Strengthen NOT-list to kill typo over-trigger | `SKILL.md` description | ❌ **reverted** (net-negative — see below) |

---

## Behavioural confirmation — eval 13 FIXED (FAIL 3/6 → PASS 6/6)

Re-ran the exact iteration-1 failure (delete-account load-bearing decision) with the reworded skill,
in two configs:

| Run | Config | `.state` | plan.md | Shipped? | spec-review.md | Verdict |
|---|---|---|---|---|---|---|
| iter-1 baseline | old skill, no hooks | `implement` | ✅ | ✅ **shipped** | ❌ absent | **FAIL 3/6** |
| **A** | reworded **+ gate hooks** | `spec` | ✗ | ✗ | ✅ present | **PASS 6/6** |
| **B** | reworded, **no hooks** | `spec` | ✗ | ✗ | ✅ present | **PASS 6/6** |

**Key results:**
- **The wording fix alone (Run B) halts** — surfaces all three load-bearing questions (+ the reviewer
  *added* "does hard-delete need a confirmation guard?"), keeps `.state=spec`, writes no plan/code,
  ships nothing, and produces **zero** assumption-language in `spec.md`.
- **The orchestration collapse is also gone** — Run B produced `spec-review.md` with
  `force_interview: true` and a populated `product_decisions_flagged[]` (iteration-1's shipping run had
  *no* `spec-review.md` at all).
- **The deterministic hook (Run A) is a working backstop** — it was present and would have blocked a
  premature `implement`, but never needed to fire because the wording stopped the loop first. This is
  the desired belt-and-suspenders outcome: register the hooks in production, but don't rely on them as
  the only thing standing between the loop and a bad ship.

**Recommendation:** ship fix #1, and make gate-hook registration the documented default (they cost
nothing when the loop isn't running and are the deterministic floor under the model-enforced rule).

---

## Triggering — settled at 18/20, with an honest caveat

Measured the description at **n=5** (n=3 proved to be decision-grade noise):

| Description | Score | Notes |
|---|---|---|
| iter-1 (with "ralph this") | 16/20 @ n=3 | baseline |
| iter-2 aggressive NOT-list | **15/20 @ n=5** | REGRESSED — suppressed positives ("implement this spec in SPEC.md" 3/3→0/5) |
| **iter-1 minus "ralph this"** ✅ | **18/20 @ n=5** | adopted |

**Two residual failures, both understood — neither is a wording bug:**
- **Typo over-trigger (3/5).** NOT controllable via the NOT-list (tested three wordings; the rate
  moved 2/3 → 0/3 → 3/5 with no consistent response). It is the inherent tension of a *deliberately
  pushy* description. **Recommended lever if you want it gone: deterministic, not probabilistic** —
  have `hooks/inject-agentic-loop-nudge.sh` skip prompts matching one-line/typo/single-file patterns.
  Blunting the pushiness in prose measurably costs legitimate triggers.
- **"LINEAR-441…get a PR up" (1/5).** Casual handoff; genuinely borderline; low priority.

**Meta-lesson:** trust n≥5 for triggering decisions on a high-variance skill, and prefer hooks over
prose for hard binary carve-outs.

---

## Net state after iteration 2
- **Behavioural:** eval 13 fixed and confirmed (both with and without hooks). Evals 6, 8, 9 still PASS.
- **Triggering:** 18/20 @ n=5; only the `"ralph this"` removal was kept from the description edits.
- **Open follow-ups (not blocking):** (a) deterministic typo-suppression in the nudge hook;
  (b) the minor iteration-1 items — spec `Risks` section (eval 6) and TDD red-green visibility (eval 8);
  (c) run the remaining CI-mode evals (7,10–12,14–22) against a real GitHub repo + Actions.

## Artifacts (iteration 2)
- `iteration-2/eval-13h-hooks/`, `iteration-2/eval-13n-nohooks/` — confirmation runs + grades
- `iteration-2/trigger-results-v2c.json` — final n=5 triggering data (18/20)
- Skill diffs: `skills/agentic-loop/SKILL.md`, `skills/agentic-loop/references/interview-protocol.md`
