---
name: validating-specs
description: >-
  Use when a spec, technical design doc, implementation plan, PRD, or task card
  needs validation or pressure-testing before implementation begins — when the
  user says "validate / review / sanity-check / pressure-test this spec", names
  the spec-design-validator agent, asks for a go/no-go on a design, or a design
  doc lands that warrants a verdict before engineering starts. Also use when the
  review should be augmented with named MCP servers or project skills passed as flags.

# Tooling: this skill is a top-level controller that DISPATCHES the
# spec-design-validator subagent. Claude Code does not allow nested subagent
# dispatch, so this skill MUST run in the main session — never invoke it from
# within a subagent. It intentionally inherits the full tool surface (Agent,
# Read, Glob, Grep, ToolSearch, AskUserQuestion, Write). No allowed-tools list
# is declared on purpose; an incomplete list would silently break dispatch.
---

# Validating Specs

You are the **controller** for validating any pre-implementation artifact — a spec, PRD,
design doc, or execution/implementation plan. You classify the artifact (type + lenses),
dispatch one or more `spec-design-validator` subagent instances (in parallel, scoped by
domain), thread in the right MCP servers and project skills, then **synthesize** their
reports into one verdict. The `spec-design-validator` agent owns the validation rubric and
anti-sycophancy protocols — you own routing, configuration, and synthesis.

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

1. **The controller is the main session.** You dispatch subagents; subagents cannot.
   Never run this skill from inside a subagent.
2. **You route and synthesize; you do NOT validate.** Do not perform your own deep
   flaw-hunt or pre-seed findings — that pollutes your context and duplicates the
   instances' job. Skim the spec only enough to classify domains and pick instance
   count. The validator instances do the actual digging.
3. **Fan out by domain, auto-scaled.** One instance for small/single-domain specs;
   split into parallel domain-scoped instances for large/multi-domain specs. Scopes
   are disjoint — each instance is told to stay in its lane.
4. **User flags always win; auto-detect augments.** MCPs/skills the user names are
   always required. You add more by scanning the spec against the detection map.
5. **One verdict out.** Merge instance reports into a single deduplicated report with
   one GO / NO-GO / REVISE verdict (most-severe-wins; a Major-only spec is a judgment
   call — see step 6).

## Workflow

### 1. Parse invocation

Invocation arguments (when the user supplies them): `<spec-path…> [--mcp a,b] [--skill x,y] [--instances N] [--split lensA,lensB] [--single]`

- **spec-path** — one or more files. If omitted, search `docs/`, `.agentic-loop/*/spec.md`,
  `*.md` for the candidate and confirm with the user before proceeding.
- **--mcp** — comma list of MCP servers to require (e.g. `context7,linear,github`).
- **--skill** — comma list of project skills to require (e.g. `your-db-skill,your-auth-skill`).
- **--instances N** / **--split a,b,c** / **--single** — override fan-out (see step 3).

Auto-trigger (no flags): treat the spec the user pointed at as the positional arg; flags are empty.

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

1. Start with the user's `--mcp` / `--skill` (always included, on every instance unless lens-irrelevant).
2. Scan spec content against `references/detection-map.md` and add matches.
3. Assign each skill/MCP to the instance(s) whose lens needs it (the map says which lens).

`context7` is the verification MCP for **version-specific, migration, or unfamiliar-library** claims.
Skip it for ubiquitous, stable libraries the validator already knows (React, Zod, Drizzle basics) unless a
specific version/API claim is actually in doubt — and query the narrowest topic, not a broad overview.

### 5. Dispatch — all instances in parallel

Send all `Agent` calls (`subagent_type: spec-design-validator`) **in a single message**.
They share an immutable spec and read-only codebase, write nothing conflicting → parallel is safe and faster.

Fill `prompts/validator-instance.md` per instance: spec path(s), assigned lens + "stay in lane",
required skills (each with the reason it's needed), required MCPs **with the ToolSearch instruction**
(subagents must `ToolSearch` the MCP tool schema before they can call it — naming the tool is not enough),
and the lens-scoped **findings-ledger** output contract (instances return findings only;
the controller writes the single human-facing 10-section report in step 6).

### 6. Synthesize (controller, main session)

1. Merge all instance reports into one findings ledger; dedup; tag each finding by lens.
2. Reconcile severities — trust cited `file:line` evidence over prose; collapse duplicates.
3. Overall verdict (most-severe-wins):
   - unfixable / foundational Blocker → **NO-GO**
   - any (fixable) Blocker → **REVISE**
   - no Blockers but ≥1 **Major** → **REVISE** if any Major must be resolved before coding can safely start; otherwise **GO**, listing the open Majors as conditions
   - only Minor / Nit findings, or clean → **GO**
4. Before writing, `Read` the agent definition at the repo-relative path `.claude/agents/spec-design-validator.md`; its **"Final deliverable structure"** section (the 10 sections) _is_ the report format — the agent file stays the single source of truth, so never inline a copy here. Emit **one** unified report in that structure, leading with the highest-impact items, tagging each finding by lens, ending in a single verdict line + rough rework estimate.
5. Offer to write it to `<spec-dir>/spec-review.md` (the repo's existing convention) — don't force.

## Quick Reference

| Situation                                      | Action                                                                             |
| ---------------------------------------------- | ---------------------------------------------------------------------------------- |
| Small doc / task card                          | 1 instance, lens `all`                                                             |
| Execution / implementation plan (`*-plan.md`)  | split: `execution` + `scope` + `architecture` (+ `security`/`domain` if triggered) |
| Design doc (`*-design.md`)                     | split: `architecture` + `domain` (+ `scope` if requirements present)               |
| Spec / PRD                                     | split: `scope` + `domain` (+ `architecture`)                                       |
| User passed `--skill your-db-skill`            | that skill required on the domain instance, even if auto-detect missed it          |
| Spec mentions a library/version                | add `context7` MCP to the relevant instance                                        |
| Spec touches signing/secrets/webhooks/auth     | add a `security` instance                                                          |
| Instance needs an MCP tool                     | prompt MUST tell it to `ToolSearch` the schema first                               |

## Common Mistakes

- **Doing the validation yourself.** You are the controller — classify, dispatch, synthesize. Deep digging is the instances' job.
- **Naming an MCP tool without the ToolSearch step.** The subagent can't call `mcp__…` until it loads the schema. Always include the ToolSearch instruction.
- **Letting auto-detect override user flags.** User `--mcp`/`--skill` are always included; auto-detect only adds.
- **Overlapping instance scopes.** Tell each instance to stay in its lane; reconcile overlaps in synthesis, not by having two instances re-litigate the same finding.
- **Folding sequencing/rollback into `scope`.** Dependency ordering, critical path, rollback, and review/test gates are the **`execution`** lens now — `scope` is requirements/acceptance-criteria only. Routing them to `scope` both under-weights them and risks a double-report.
- **Classifying doc-type by directory.** `docs/plans/` holds both plans and designs — use the `*-plan`/`*-design`/`*-spec` suffix or content headings, never the folder.
- **Running this inside a subagent.** Nesting isn't allowed — the controller is the main session.
- **Emitting N reports.** The user gets one merged report and one verdict.

## Files

- `references/detection-map.md` — spec-content → skill/MCP mapping, and which lens each serves
- `prompts/validator-instance.md` — the templated prompt sent to each `spec-design-validator` instance
