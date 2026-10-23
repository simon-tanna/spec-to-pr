---
name: diataxis-docs
description: >-
  Diátaxis docs grounded in this repository's code: sorts each document into
  one quadrant (tutorial, how-to, reference, explanation), verifies every claim
  against source, and mirrors the repo's docs layout. Use when writing docs or a
  README for code in the working repo, or when improving, auditing, or
  restructuring an existing doc set that mixes teaching, tasks, and reference.
---

# Diátaxis docs

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

A README or docs index is a landing page, not a quadrant: what the project
is, how to install it, one minimal example, and links into the set. Anything
longer moves to its quadrant document.

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

Verify what you are about to document — or, when improving, what the existing
docs claim — actually exists; in §4 do this per document during the audit. Read
the relevant source, config, schema, routes, and tests in the repo. Confirm
every endpoint, header, flag, command, config field, and return shape against
real code before you state it — do not infer an API surface from convention.
For library/framework/SDK/CLI facts, ground against the version pinned in the
repo's lockfile: use the Context7 MCP when available, otherwise the installed
package source; say which you used. Then:

- If the feature exists, write only what you grounded. List the files each
  document's claims rest on in the §3 step 2 proposal (or the §4 step 2 move
  list); put source links inside a document only where the repo's existing
  docs already do.
- If it is **partially built or planned**, say so explicitly and mark those
  sections "Not yet implemented" rather than describing them as working.
- If it **does not exist**, do not invent it — tell the user and ask how they
  want to proceed.

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
   the user has told you to proceed without review.
3. **Write each document to its agreed path**, one at a time, in the format the
   repo's existing docs use (Markdown if none).
4. **Re-read each finished draft against its own quadrant file**, applying every
   Craft rule and every "Done when" item in that file. Move anything serving a
   different quadrant into its own document in the set.
5. **Cut pass.** Re-read each draft line by line against its quadrant file's
   Register and LANGUAGE AND STYLE; cut every word whose removal loses no
   meaning. Run this pass in a fresh child instead when this session has
   compacted since §1 or the user asked for independent review: spawn one
   with your host's agent tool (Claude: a general-purpose Agent; Codex: a
   child agent with a fresh context), paste the draft, its quadrant file, and
   LANGUAGE AND STYLE into the prompt (children inherit none of this skill),
   and have it return the revised text without editing files or spawning
   children. Call the pass independent only when a child actually ran it.

Done when every technical claim is grounded in §1, every document passes its
quadrant's "Done when", and every line has survived the step 5 cut pass.

### 4. Improving

1. **Audit exhaustively.** Read every document in scope. Read the quadrant files
   you are judging against — the same four linked in §3 — so purity is assessed
   against stated criteria rather than memory. For each document: assign a
   quadrant, name every section serving a different one, and ground its technical
   claims per §1 — a doc set restructured while still describing software that
   changed is tidied, not fixed. Done when every document has a quadrant and
   every mixed section is named.
2. **Propose an ordered move list, and wait for approval.** This is the gate.
   Each move small and separately reviewable: split this page, move that section,
   relocate a file into the layout found in §1, retitle, correct this claim.
   Order by what unblocks the rest.
3. **Apply the moves one at a time.** Once each move lands, re-read every
   touched document against its quadrant file, and run §3 step 5's cut pass
   over any text you wrote. Restructure move by move, never in one sweep.

Done when every approved move is applied, every touched document passes its
quadrant's "Done when", and every corrected claim is grounded per §1.

## LANGUAGE AND STYLE

Register belongs to the quadrant file. The rules below hold in every quadrant
and yield to it where they meet.

- Omit needless words: cut preamble, wrap-up, and hedges.
- Active voice; definite, specific, concrete language.
- Strike on sight: *the fact that*, *in the case of*, *of a … nature* /
  *character*, *factor*, *feature*, *very*, *certainly*, *interesting*,
  *as to whether*, *along these lines*, *one of the most*.
- Take terminology from the user's other Markdown files; take register only
  from the quadrant file.

| Draft | Revised |
|---|---|
| In this guide, we will walk through setting up the webhook. | *(cut)* |
| The retry queue is maintained on a per-tenant basis, which prevents a single tenant from starving the others. | Retries queue per-tenant, so one tenant cannot starve the others. |
