# Validating Specs

You are the **controller** for validating any pre-implementation artifact — a spec, PRD,
design doc, or execution/implementation plan. You classify the artifact (type + lenses),
dispatch one or more `spec-design-validator` subagent instances (in parallel, scoped by
domain), thread in the right MCP servers and project skills, then **synthesize** their
reports into one verdict. The bundled `references/validator-role.md` owns the validation rubric and
anti-sycophancy protocols — you own routing, configuration, and synthesis.

Read `references/dispatch.md` before dispatch. Resolve all references from this
installed skill directory and pass absolute paths (or their complete content) to
children. Native agent registration is optional. Each validator receives the
bundled role plus its filled instance prompt; a native name alone is insufficient.
If fresh child dispatch or a required capability is unavailable, stop with setup
guidance; never replace the independent validation with controller self-review.

**Announce at start:** "Validating this spec via the validating-specs skill."

## When to Use

- A spec / design doc / implementation plan / PRD / task card needs a go/no-go before coding
- The user asks to validate, review, pressure-test, or sanity-check a spec
- The user wants the review to use specific MCPs/skills (passed as flags) or expects auto-detection

## When NOT to Use

- Reviewing already-written **code** → use `code-reviewer` / `/review` / `security-review`
- Implementing a spec end-to-end → that's `agentic-loop` (which calls the validator itself; don't double-run)
- Trivial specs (a few lines, single obvious change) → just read it and respond directly

## Core Principles

1. **The controller is the main session.** You dispatch subagents; children must not delegate further.
   Never run this skill from inside a subagent.
2. **You route and synthesize; you do NOT validate.** Do not perform your own deep
   flaw-hunt or pre-seed findings — that pollutes your context and duplicates the
   instances' job. Skim the spec only enough to classify domains and pick instance
   count. The validator instances do the actual digging.
3. **Fan out by domain, auto-scaled.** One instance for small/single-domain specs;
   split into parallel domain-scoped instances for large/multi-domain specs. Scopes
   are disjoint — each instance is told to stay in its lane.
4. **User-named tooling always wins; auto-detect augments.** Any MCP/skill the user names —
   whether via a `--mcp`/`--skill` flag **or in prose** ("…and use context7 for this") — is always
   required on every lens-relevant instance; auto-detect (the detection map) may only _add_, never drop
   one. A `--token` outside the known grammar `{mcp, skill, instances, split, single}` is **echoed back
   as an unrecognised flag and the run still proceeds** (so a typo like `--skil` is never silently
   swallowed); a named value that resolves to no real skill/MCP is **surfaced to the user**, not quietly
   dropped.
5. **One verdict out.** Merge instance reports into a single deduplicated report with
   one GO / NO-GO / REVISE verdict (most-severe-wins; a Major-only spec is a judgment
   call — see step 6).

## Workflow

### 1. Parse invocation

Invocation arguments (when the user supplies them): `<spec-path…> [--mcp a,b] [--skill x,y] [--instances N] [--split lensA,lensB] [--single]`

The raw invocation string is delivered right here, at the parse step:

```
$ARGUMENTS
```

In Claude Code, read a substituted fenced argument string above. In other harnesses,
read the actual skill invocation and user request. An empty or literal placeholder
is not input: it does not erase flags supplied in the user's request. Parse once;
honor tooling named in prose as well as flags. Never interpret the placeholder as
an executable command or a path.

- **spec-path** — one or more files. If omitted, search `docs/`, `.agentic-loop/*/spec.md`,
  `*.md` for the candidate and confirm with the user before proceeding.
- **--mcp** — comma list of MCP servers to require (e.g. `context7,linear,github`).
- **--skill** — comma list of project skills to require (e.g. `your-db-skill,your-auth-skill`).
- **--instances N** / **--split a,b,c** / **--single** — override fan-out (see step 3).

Auto-trigger (no flags): treat the spec the user pointed at as the positional arg; flags are empty —
but still honour any MCP/skill the user named in prose (Core Principle 4).

### 2. Classify (skim only — do NOT validate)

Read the spec quickly to determine: which **lenses** it touches, its size, and which
skills/MCPs are relevant. Do not produce findings yet.

### 2.5 Classify doc-type

Identify which of four artifact types you're validating — it sets the **default lens split**
(step 3). Classify by **filename suffix first**, then **content** when the suffix is absent:

- **Suffix** — `*-plan.md` → execution plan; `*-design.md` → design doc; `*-spec*` / `*-prd*` → spec/PRD.
- **Content fallback** (for off-convention docs) — headings/structure like `## Task N`, `## Phase N`,
  or sequenced steps ⇒ **execution plan**; `## Decisions`, `## Module Structure`, `## Test Strategy` ⇒
  **design doc**; requirements + acceptance-criteria blocks ⇒ **spec/PRD**; a few lines / one ask ⇒ **task card**.

Do **NOT** classify by directory — e.g. `docs/plans/` holds both `*-plan.md` and `*-design.md` for the
same change, so the directory tells you nothing. If the doc is genuinely unclassifiable, skip the
doc-type bias and fall back to the size-based default in step 3.

### 3. Decide fan-out

The five canonical lenses (mirror the validator's own domains), each scoped **disjoint** — no
two lenses own the same surface, so parallel instances never re-litigate the same finding:

| Lens             | Covers                                                                                                                            | Include when                                                                 |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **architecture** | codebase fit, component boundaries, package/monorepo conventions, data flow                                                       | always                                                                       |
| **domain**       | project-specific semantics (your core business rules, workflows, invariants, auth model)                                          | spec encodes domain logic                                                    |
| **scope**        | requirements, scope boundaries, out-of-scope declarations, acceptance criteria, test-plan coverage                                | always                                                                       |
| **execution**    | dependency ordering, critical path, parallelizable workstreams, estimate realism, rollback/migration, rollout & review/test gates | artifact is an execution/implementation plan or has phased rollout/migration |
| **security**     | auth, signing/KMS/JWS, secrets, webhook verification, injection/attack surface                                                    | spec touches any of these                                                    |

**Boundary (scope vs execution):** `scope` owns _what_ must be true (requirements, acceptance
criteria, test-plan **coverage**). `execution` owns _how/when_ it gets built (sequencing, critical
path, rollback, review/test **gates**, estimates). Sequencing and gates live in `execution` only —
never duplicate them under `scope`.

Sizing rule (overridable by flags):

- `--single`, or spec is **small (≈<150 lines)** or a **task card** → **1 instance**, lens = `all`. A short
  doc gets one all-lenses pass even when it touches several lenses — never spawn multiple agents for a brief doc.
- Otherwise → **one instance per touched lens**, capped at **5** (the full canonical set). The default
  split is **driven by doc-type** (step 2.5):

  | Doc-type       | Default split                                                 |
  | -------------- | ------------------------------------------------------------- |
  | execution plan | `execution` + `scope` + `architecture`                        |
  | design doc     | `architecture` + `domain` (+ `scope` if requirements present) |
  | spec / PRD     | `scope` + `domain`                                            |
  | unclassified   | `architecture` + `scope` (size-based fallback)                |

  Always add `security` when its trigger keywords appear; add `domain` when the doc encodes
  project-specific business logic. Five disjoint lenses ⇒ cap 5 ⇒ no silent lens-drop.

- `--instances N` caps/forces the count; `--split a,b,c` forces exact lenses; both override the doc-type default.

### 4. Resolve MCPs/skills per instance

Build the required-tooling set for each instance:

1. Start with user-named tooling — the `--mcp` / `--skill` flags **or** anything the user asked for in
   prose (always included, on every instance unless lens-irrelevant).
2. Scan spec content against `references/detection-map.md` and add matches.
3. Assign each skill/MCP to the instance(s) whose lens needs it (the map says which lens).

`context7` is the verification MCP for **version-specific, migration, or unfamiliar-library** claims.
Skip it for ubiquitous, stable libraries the validator already knows (React, Zod, Drizzle basics) unless a
specific version/API claim is actually in doubt — and query the narrowest topic, not a broad overview.
User/project instructions requiring Context7 more broadly take precedence. Required
MCP access must be verified inside the fresh child; parent access is not proof.

### 5. Dispatch — fresh instances within available capacity

Follow `references/dispatch.md`. Load `references/validator-role.md` and fill
`prompts/validator-instance.md` for each lens. Supply both to each fresh child,
with absolute spec/resource paths, required tooling, and the findings-ledger
contract. Claude may use its registered validator or a generic child with the
bundled role; Codex uses the exposed spawn interface with the role in its task.

Dispatch independent read-only lenses concurrently within available slots; queue
remaining lenses. Collect every required lens before synthesis. Children return
findings without writing files or memory. Read-only instructions are a behavior
contract, not a claim of sandbox enforcement. Ask each child to verify required
tools by actual use before dependent analysis; use the available discovery API
for deferred tools. If access fails, report the missing capability and stop.

### 6. Synthesize (controller, main session)

1. Merge all instance reports into one findings ledger; dedup; tag each finding by lens.
2. Reconcile severities — trust cited `file:line` evidence over prose; collapse duplicates.
3. Overall verdict (most-severe-wins):
   - unfixable / foundational Blocker → **NO-GO**
   - any (fixable) Blocker → **REVISE**
   - no Blockers but ≥1 **Major** → **REVISE** if any Major must be resolved before coding can safely start; otherwise **GO**, listing the open Majors as conditions
   - only Minor / Nit findings, or clean → **GO**
4. Read the bundled `references/report-format.md` and emit one unified report in
   its structure, leading with the highest-impact items, tagging findings by lens,
   and ending in one verdict plus a rough rework estimate where justified. No
   repository `.claude/agents/` path or native registration is required.
5. If an output path was supplied, write the merged report there. Otherwise offer
   `<spec-dir>/spec-review.md`; do not write an unrequested report automatically.

## Quick Reference

| Situation                                     | Action                                                                             |
| --------------------------------------------- | ---------------------------------------------------------------------------------- |
| Small doc / task card                         | 1 instance, lens `all`                                                             |
| Execution / implementation plan (`*-plan.md`) | split: `execution` + `scope` + `architecture` (+ `security`/`domain` if triggered) |
| Design doc (`*-design.md`)                    | split: `architecture` + `domain` (+ `scope` if requirements present)               |
| Spec / PRD                                    | split: `scope` + `domain` (+ `architecture`)                                       |
| User passed `--skill your-db-skill`           | that skill required on the domain instance, even if auto-detect missed it          |
| Spec mentions a library/version               | add `context7` MCP to the relevant instance                                        |
| Spec touches signing/secrets/webhooks/auth    | add a `security` instance                                                          |
| Instance needs an MCP tool                    | verify actual child access; discover deferred schemas through the exposed interface                               |

## Common Mistakes

- **Doing the validation yourself.** You are the controller — classify, dispatch, synthesize. Deep digging is the instances' job.
- **Assuming parent tools imply child access.** Verify access in the child and discover deferred schemas with the interface actually exposed; Claude ToolSearch names are not portable.
- **Letting auto-detect override user-named tooling.** Anything the user names — `--mcp`/`--skill` flag or prose — is always included; auto-detect only adds. Echo unrecognised `--tokens`; surface unresolvable names.
- **Overlapping instance scopes.** Tell each instance to stay in its lane; reconcile overlaps in synthesis, not by having two instances re-litigate the same finding.
- **Folding sequencing/rollback into `scope`.** Dependency ordering, critical path, rollback, and review/test gates are the **`execution`** lens now — `scope` is requirements/acceptance-criteria only. Routing them to `scope` both under-weights them and risks a double-report.
- **Classifying doc-type by directory.** `docs/plans/` holds both plans and designs — use the `*-plan`/`*-design`/`*-spec` suffix or content headings, never the folder.
- **Running this inside a subagent.** This workflow keeps all dispatch in the main-session controller on every harness.
- **Emitting N reports.** The user gets one merged report and one verdict.

## Files

- `references/detection-map.md` — spec-content → skill/MCP mapping, and which lens each serves
- `prompts/validator-instance.md` — the templated prompt sent to each `spec-design-validator` instance

- `references/dispatch.md` — harness capability and fresh-child contract
- `references/validator-role.md` — complete portable validation rubric
- `references/report-format.md` — controller report structure
