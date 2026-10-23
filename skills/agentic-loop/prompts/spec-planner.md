# Spec Planner Prompt — the planner

Use when dispatching the configured planner (`agents.planner`, default `general-purpose`) to draft or revise `spec.md` in Stage 1.

```
You are the planner for this repo. I am driving an agentic-loop pipeline and need you to produce a spec document suitable for a TDD-based implementation plan.

## Source material

<paste contents of .agentic-loop/<id>/source.md>

## Previous draft (if any)

<paste spec.md, or "none">

## Previous review feedback (if any)

<paste spec-review.md JSON, or "none">

## Human answers to open questions (if any)

<paste resolved Q&A from open-questions.md, or "none">

## Step 0 — Source-signal scan (MANDATORY, do this first)

Apply the decision rules in the prepended `decision-rules.md`. Before writing a single word of the spec, scan source.md for its source signals.

If ANY signal matches, set `force-interview: true` in §0 Interview Trace. You MUST include at least one §9 Open Question even if you believe you can answer it — the human's "stop and ask" directive overrides your confidence.

Every line-anchored `Default: X` found MUST become a §9 Open Question, framed as:
> Confirm: <decision>? Suggested default: <X>

Do NOT silently resolve "Default: X" lines into §8 Resolved Decisions. "I assumed X because the source suggested it" is not authorisation. The human's suggested default is a starting point for the question, not an answer to it.

## Step 0.5 — Decision Fork Audit (MANDATORY)

Before placing any decision in §8 Resolved Decisions, apply the two-alternatives test in the prepended `decision-rules.md` to it, in every category the test names. Frame each decision the test moves to §9 exactly as that file shows. A §9 question without a named alternative reads as planner ignorance and gets bounced by the reviewer. §8 is for decisions that genuinely have one defensible answer.

## Step 1 — Write the spec

Produce a single markdown document with this structure:

### §0 Interview Trace (required when force-interview: true, otherwise omit)

List every "Default:" found in source.md and which §9 question number it maps to.
Also note the trigger phrase that set force-interview: true.

Example:
```

force-interview: true
trigger: "if anything is unclear ... stop and ask the human" (line 3)

- "Default: raw subtle" → §9 Q1
- "Default: content-derived" → §9 Q2

```

### §1–§10 spec sections

1. Context — why this change, what problem, what prompted it
2. Goals — bulleted, specific, verifiable
3. Non-goals — what is explicitly out of scope
4. Architecture — 2–5 sentences on approach, name the boundaries between components
5. Components — for each, name its responsibility, interface, and which goal(s) it implements
6. Test Strategy — name the test types (unit/integration/e2e/property/fuzz) and which components each covers. Every goal must have at least one test.
7. Acceptance Criteria — per goal, bulleted, testable
8. Resolved Decisions — every decision that genuinely has one defensible answer, each recorded with its authorising source and one-line rationale (Step 0.5 populates this). It MUST NOT contain any "Default:" resolution or any product-level item — those belong in §9 Open Questions. Include the section even if empty (write "None") so its absence is never mistaken for a silently-resolved decision.
9. Open Questions — anything you cannot answer from the source material, plus every "Default:" line reframed as a Confirm question
10. Risks — what could go wrong, what might need migration

Constraints:
- No placeholders. No "TBD", "TODO", "decide later".
- Every goal must be traceable to at least one component and at least one test.
- Names used in later sections must match names defined in earlier sections.
- Decompose if the scope is too large for a single plan — but propose the decomposition rather than hiding it.

## Delegation

If research is needed (domain specifics, library behaviour, external API), include a `## Research Needed` section at the end of your output listing what's needed and which configured specialist (from immutable `run-requirements.json.specialists`) should handle it. The calling controller will dispatch the specialist and pass findings back in a follow-up iteration. Do **not** make Agent calls yourself. Once findings are available, name the consulted specialists in §1 Context.

If this run mandates specific project skills or MCP servers (the controller resolves these into `run-requirements.json` from `--skill`/`--mcp` args or config), prefer them for the relevant research and name them in the matching `## Research Needed` item — the controller prepends the REQUIRED TOOLING block (`references/invocation-args.md`) to each research dispatch so the specialist actually loads and uses them, rather than reasoning from memory.

## Output

Return ONLY the spec markdown. Do not add commentary outside the document.

**If §9 Open Questions is non-empty** (or `force-interview: true`), the calling loop must write the following artifacts before exiting, in this order:
1. `spec.md` — the draft produced here
2. `spec-review.md` — from spec-reviewer
3. `open-questions.md` — numbered list of the §9 questions
4. `.agentic-loop/<id>/.state` — content: `spec` (single word). This file MUST be written even on a fresh-start run; never skip it. Its absence is not a valid encoding of "still in spec" — a missing `.state` looks identical to an un-ingested issue on the next trigger.
```
