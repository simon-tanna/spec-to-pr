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

Before placing any decision in §8 Resolved Decisions or any exclusion in §3 Non-goals, apply the two-alternatives test in the prepended `decision-rules.md` to it, in every category the test names. Frame each decision the test moves to §9 exactly as that file shows. A §9 question without a named alternative reads as planner ignorance and gets bounced by the reviewer. §8 is for decisions that genuinely have one defensible answer.

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
3. Non-goals — what is explicitly out of scope; each exclusion is a choice and carries its Step 2 basis tag
4. Architecture — 2–5 sentences on approach, name the boundaries between components
5. Components — for each, name its responsibility, interface, and which goal(s) it implements
6. Test Strategy — name the test types (unit/integration/e2e/property/fuzz) and which components each covers. Every goal must have at least one test.
7. Acceptance Criteria — per goal, bulleted, testable
8. Resolved Decisions — every decision that genuinely has one defensible answer, numbered D1, D2, …, each recorded with its authorising source and one-line rationale (Step 0.5 populates this). It MUST NOT contain any "Default:" resolution or any product-level item — those belong in §9 Open Questions. Include the section even if empty (write "None") so its absence is never mistaken for a silently-resolved decision.
9. Open Questions — one numbered list: anything you cannot answer from the source material, plus every "Default:" line reframed as a Confirm question. Every question blocks planning until the human answers it; its suggested default is where the human starts, and the plan waits for the answer
10. Risks — what could go wrong, what might need migration

Constraints:
- No placeholders. No "TBD", "TODO", "decide later".
- Every goal must be traceable to at least one component and at least one test.
- Names used in later sections must match names defined in earlier sections.
- Decompose if the scope is too large for a single plan — but propose the decomposition rather than hiding it.

## Step 2 — Basis audit (MANDATORY, before you return)

Walk §2–§7 and §10 sentence by sentence. A *choice* is any sentence that settles something source.md does not literally state: a behaviour, an exclusion, where logic lives, a name, a route, an actor, a number. End each choice with its basis tag:

- `[source L<n>]`: that source.md line authorises it, as `decision-rules.md` defines authorisation.
- `[§8 D<n>]`: a one-option decision recorded in §8.
- `[Q<n> default]`: the suggested default of §9 question n; the sentence holds only if the human accepts that default.

A choice without a basis gets one now: add the §9 Confirm question (or, for a one-option choice, the §8 entry) and tag the sentence. A §10 risk that needs a decision gets its §9 question the same way.

Done when every choice in §2–§7 and §10 carries a tag and every `[Q<n> default]` and `[§8 D<n>]` names an entry that exists.

## Delegation

If research is needed (domain specifics, library behaviour, external API), include a `## Research Needed` section at the end of your output listing what's needed and which configured specialist (from immutable `run-requirements.json.specialists`) should handle it. The calling controller will dispatch the specialist and pass findings back in a follow-up iteration. Do **not** make Agent calls yourself. Once findings are available, name the consulted specialists in §1 Context.

If this run mandates specific project skills or MCP servers (the controller resolves these into `run-requirements.json` from `--skill`/`--mcp` args or config), prefer them for the relevant research and name them in the matching `## Research Needed` item — the controller prepends the REQUIRED TOOLING block (`references/invocation-args.md`) to each research dispatch so the specialist actually loads and uses them, rather than reasoning from memory.

## Output

Return ONLY the spec markdown. Do not add commentary outside the document.
```
