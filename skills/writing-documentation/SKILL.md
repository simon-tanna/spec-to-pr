---
name: writing-documentation
description: >-
  Diátaxis technical documentation — writes new docs, and audits existing ones
  for quadrant purity and accuracy. Use when the user asks to write or improve
  documentation, a README, a tutorial, a how-to guide, reference pages, or
  explanatory content; or when a doc set mixes teaching, tasks, and reference in
  one page. Triggers on: write docs, document this, write README, write tutorial,
  how-to guide, reference documentation, explain concept, improve the docs,
  restructure the docs, Diátaxis.
---

# Diátaxis Documentation Expert

Your work is guided by the Diátaxis Framework (https://diataxis.fr/).

## The compass

Every document belongs to exactly one **quadrant**. Two questions place it:

1. **Action or cognition?** Does the content inform what the reader *does*, or
   what they *know*?
2. **Acquisition or application?** Is the reader *studying*, or *working*?

| Informs | Serves | Quadrant |
|---|---|---|
| action | acquisition of skill | **Tutorial** — a lesson |
| action | application of skill | **How-to guide** — a recipe |
| cognition | application of skill | **Reference** — a dictionary |
| cognition | acquisition of understanding | **Explanation** — a discussion |

Answer both questions before writing a line. A document you cannot place is a
document carrying more than one quadrant — split it.

## Purity

**One quadrant per document.** A lesson that stops to explain, a recipe that
swells into a parameter table, a dictionary that starts instructing — each
breaks the reader's flow at the moment they were relying on it, and each is the
failure Diátaxis exists to catch.

Material belonging to another quadrant is not deleted. It moves to its own
document in the set, and the two link.

## WORKFLOW

Every document serves one reader reaching one goal — hold that reader in view
throughout.

### 1. Ground first (REQUIRED — do this before writing anything)

Verify what you are about to document actually exists. Read the relevant source,
config, schema, routes, and tests in the repo. Confirm every endpoint, header,
flag, command, config field, and return shape against real code before you state
it — do not infer an API surface from convention. For library/framework/SDK/CLI
facts, use the Context7 MCP (not for general programming concepts). Then:

- If the feature exists, write only what you grounded, citing the files you
  grounded in.
- If it is **partially built or planned**, say so explicitly and mark those
  sections "Not yet implemented" rather than describing them as working.
- If it **does not exist**, do not invent it — tell the user and ask how they
  want to proceed.
- When the user provides other Markdown files, use them for the project's
  existing tone and terminology — do not copy their content unless asked.

While grounding, note **where this repo already keeps documentation** and mirror
that placement. Do not scaffold empty quadrant directories and wait for them to
fill; structure emerges as material accumulates.

### 2. Take the branch

- Writing new documentation → **§3 Writing**.
- Improving documentation that already exists → **§4 Improving**.

### 3. Writing

1. **Determine the document set.** Run the compass over the request. One request
   often yields more than one document — "document the payments webhook" is a
   How-to *and* a Reference, perhaps an Explanation. For each document, read its
   quadrant file —
   [tutorial](references/quadrant-tutorial.md) ·
   [how-to](references/quadrant-how-to.md) ·
   [reference](references/quadrant-reference.md) ·
   [explanation](references/quadrant-explanation.md)
   — which carries that quadrant's craft, register, title shape, and completion
   bound. Then name each document's quadrant, title, and path, with a short outline.
2. **Propose the set and wait for approval.** This is the gate: a mis-sorted
   quadrant is cheapest to catch here, before any prose exists. Skip it only when
   the user says "just write it".
3. **Write each document to its agreed path**, one at a time, in Markdown.
4. **Re-read each finished draft against its own quadrant file**, applying every
   item in that file's "Done when". Move anything serving a different quadrant
   into its own document in the set.

Done when every technical claim is grounded in §1, every document passes its
quadrant's "Done when", and every line has survived a cut pass against LANGUAGE
AND STYLE.

### 4. Improving

1. **Audit exhaustively.** Read every document in scope. Read the quadrant files
   you are judging against — the same four linked in §3 — so purity is assessed
   against stated criteria rather than memory. For each document: assign a
   quadrant, name every section serving a different one, and ground its technical
   claims against source as you go — a doc set restructured while still
   describing software that changed is tidied, not fixed. Done when every
   document has a quadrant and every mixed section is named.
2. **Propose an ordered move list, and wait for approval.** This is the gate.
   Each move small and separately reviewable: split this page, move that section,
   relocate a file into the layout found in §1, retitle, correct this claim.
   Order by what unblocks the rest.
3. **Apply the moves one at a time**, re-reading each touched document against its
   quadrant file once its move lands. Restructure a working doc set move by move,
   never in one sweep.

## LANGUAGE AND STYLE

**Register is set by the quadrant** — telegraphic for Reference and How-to, plain
and economical for Tutorial and Explanation. The quadrant file is authoritative;
read it before drafting.

### Shared rules

These hold in all four quadrants. Concision rules that belong to one register —
one idea per line, cut anything the heading already said — live in the
telegraphic quadrant files, not here.

- Cut preamble, wrap-up, and hedges.
- Use the active voice.
- Put statements in positive form — make definite assertions.
- Use definite, specific, concrete language.
- Express co-ordinate ideas in parallel form.
- Keep related words together; place emphatic words at the sentence's end.

| Draft | Revised |
|---|---|
| In this guide, we will walk through setting up the webhook. | *(cut)* |
| The retry queue is maintained on a per-tenant basis, which prevents a single tenant from starving the others. | Retries queue per-tenant, so one tenant cannot starve the others. |

[references/elements-of-style.md](references/elements-of-style.md) is
authoritative for the full 18 rules **and** the _Words and Expressions Commonly
Misused_ usage dictionary — pull it into context for a rule's full text or a
usage ruling.

**Limited-context fallback:** dispatch a subagent with your draft, this section,
and the draft's quadrant file. Have it check quadrant conformance first, cut to
the quadrant's register second, copyedit third, and return the revision.
