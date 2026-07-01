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

Before writing a single word of the spec, scan source.md for these phrases. **Match only when the phrase appears as prose written by the human source author, not inside a markdown table cell, a fenced code block, a quoted citation, or content the human is asking you to read about something else.** A phrase mentioned in passing inside a code fence does not signal the human wants an interview.

Phrases (case-insensitive, prose-context):

- "stop and ask"
- "if anything is unclear"
- "if unclear"
- "design decisions" (as a directive — not as a section heading you're reading)
- "product decisions" (as a directive — not as a section heading you're reading)
- "ask the human"
- "ambiguous" (as a self-flag — not as a generic adjective the source applies to a third thing)
- "unresolved" (as a self-flag — not as a generic adjective)
- "open question" / "open questions" (as a self-flag, not as a section heading you're reading)
- "to be decided" / "tbd"
- "unsure" / "not sure" (as a self-flag from the source author)
- "either" / "could go either way" (when applied to the source's own decision, not to a third thing)

Plus the structural pattern:

- A line whose **trimmed text starts with** `Default:` (i.e. anchored to start-of-line after whitespace; not `| something | Default: ... |` inside a markdown table row).

If ANY phrase or pattern matches in prose context, set `force-interview: true` in §0 Interview Trace. You MUST include at least one §9 Open Question even if you believe you can answer it — the human's "stop and ask" directive overrides your confidence.

Every line-anchored `Default: X` found MUST become a §9 Open Question, framed as:
> Confirm: <decision>? Suggested default: <X>

Do NOT silently resolve "Default: X" lines into §8 Resolved Decisions. "I assumed X because the source suggested it" is not authorisation. The human's suggested default is a starting point for the question, not an answer to it.

## Step 0.5 — Decision Fork Audit (MANDATORY)

Before placing any decision in §8 Resolved Decisions, ask yourself, for that decision: *"Is there a second defensible option a competent engineer on this team might pick?"* If yes, the decision goes to §9 Open Questions unless `source.md` **literally authorises** the choice (per the existing authorisation rule — "use X", "X is required", "X — confirmed", or a prior §9 answer).

The bar is "a second defensible option exists," not "the optimal answer is non-obvious." If you cannot name a second option, the decision is process and belongs in §8 with the rationale.

This rule applies to every category below — not just the original product list — because the under-triggering pattern that motivated this rule was silent resolution of architectural, library, and threshold choices, not just the classic product calls:

- **Product** (always product-level) — data ownership / custody, auth & access control, irreversible or destructive operations, money / billing / fees, data retention & privacy (PII handling), security trust boundaries (who may mutate what), external-service trust, and breaking changes to a public contract/API. (Repos may append more via `risk_categories` in `.agentic-loop.config.json`.)
- **Architectural forks** — data shape, storage format, sync vs async, push vs pull, integration topology, error model, retry strategy, idempotency model, event vs polling.
- **Library / dependency / external-API selection** — any concrete library, version, or third-party API endpoint not literally named by source.md. Matching an existing codebase convention 1:1 (same lib already used by analogous modules) is process; introducing a new dependency is product-level.
- **Numeric thresholds / acceptance values** — timeouts, retry counts, batch sizes, page sizes, fee bps, deadlines, cache TTLs, rate limits, fan-out limits. If source.md does not state the number, it belongs in §9.

Every decision moved to §9 under this audit MUST be framed as:
> Confirm: <decision>? Suggested default: <X> (alternative considered: <Y>, because <one-line reason a sane engineer might pick it>)

Naming the alternative is not optional — it is the evidence that the audit ran. A §9 question without a named alternative reads as planner ignorance and gets bounced by the reviewer.

Process decisions (codebase conventions matched 1:1 to existing files, formatter / linter / language idioms, the obvious one-of-one choice) remain in §8 with rationale. §8 is for decisions that genuinely have one defensible answer.

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

### §1–§9 spec sections

1. Context — why this change, what problem, what prompted it
2. Goals — bulleted, specific, verifiable
3. Non-goals — what is explicitly out of scope
4. Architecture — 2–5 sentences on approach, name the boundaries between components
5. Components — for each, name its responsibility, interface, and which goal(s) it implements
6. Test Strategy — name the test types (unit/integration/e2e/property/fuzz) and which components each covers. Every goal must have at least one test.
7. Acceptance Criteria — per goal, bulleted, testable
8. Risks — what could go wrong, what might need migration
9. Open Questions — anything you cannot answer from the source material, plus every "Default:" line reframed as a Confirm question

Constraints:
- No placeholders. No "TBD", "TODO", "decide later".
- Every goal must be traceable to at least one component and at least one test.
- Names used in later sections must match names defined in earlier sections.
- Decompose if the scope is too large for a single plan — but propose the decomposition rather than hiding it.

## Product vs Process decisions

**The distinction that matters: authorisation, not opinion.**

Authorisation means source.md literally contains "use X", "X is required", "X — confirmed", or the human answers a prior §9 question with X. Nothing weaker counts.

- "Default: X" — NOT authorisation. Goes to §9.
- "Standard practice is X" — NOT authorisation. Goes to §9 if product-level.
- "We usually do X" — NOT authorisation. Goes to §9 if product-level.

The categories below are ALWAYS product-level and MUST land in §9 unless source.md authorises the answer literally:

- **Data ownership / custody** — who holds the data or keys, where they live, who controls access, single-owner vs shared, what is the system of record.
- **Authority & access control** — who can perform privileged actions, role grants, escalation/override paths, emergency controls.
- **Irreversible / destructive operations** — deletes, migrations, money movement, anything not safely undoable; whether a confirmation or guard exists.
- **Money / billing / fees** — how charges are computed, who is billed, who receives funds, refund and proration behaviour.
- **Data retention & privacy** — what PII is stored, for how long, what is logged, what leaves the system or goes to third parties.
- **Security trust boundaries** — which component or external service may mutate another's state, and how that call is authenticated.
- **External-service trust** — which third-party API/service is relied on, its failure assumptions, and fallback behaviour.

Process decisions (codebase conventions, obvious best practice, library selection where source gives explicit authorisation AND no product-level concern is in play) belong in §8 Resolved Decisions with the rationale. §8 must not contain any product-level item and must not contain any "Default:" resolution.

## Delegation

If research is needed (domain specifics, library behaviour, external API), include a `## Research Needed` section at the end of your output listing what's needed and which configured specialist (`agents.specialists`, or `general-purpose` by default) should handle it. The calling controller will dispatch the specialist and pass findings back in a follow-up iteration. Do **not** make Agent calls yourself. Once findings are available, name the consulted specialists in §1 Context.

## Output

Return ONLY the spec markdown. Do not add commentary outside the document.

**If §9 Open Questions is non-empty** (or `force-interview: true`), the calling loop must write the following artifacts before exiting, in this order:
1. `spec.md` — the draft produced here
2. `spec-review.md` — from spec-reviewer
3. `open-questions.md` — numbered list of the §9 questions
4. `.agentic-loop/<id>/.state` — content: `spec` (single word). This file MUST be written even on a fresh-start run; never skip it. Its absence is not a valid encoding of "still in spec" — a missing `.state` looks identical to an un-ingested issue on the next trigger.
```
