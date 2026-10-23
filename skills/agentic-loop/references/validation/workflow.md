# Validating Specs

<!-- Generated from skills/validating-specs/SKILL.md by scripts/build-distribution.py. Maintainers: edit the canonical file and rebuild. -->

You are the **controller**: you classify the artifact, dispatch fresh `spec-design-validator` instances (one per lens), and synthesize their ledgers into one report and one verdict. The instances own every finding; your reading of the spec ends at classification (step 2).

Resolve every `references/` and `prompts/` path in this file relative to the directory containing this file, and hand children absolute paths. Run this workflow in the main session; children return ledgers and never delegate.

## Workflow

### 1. Parse invocation

Invocation arguments (when the user supplies them): `<spec-path…> [--context path,…] [--out path] [--mcp a,b] [--skill x,y] [--instances N] [--split lensA,lensB] [--single]`

When another skill loaded this file, that skill's instructions supply the arguments; skip `$ARGUMENTS`.

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
- **--context** — documents the validators read for reference only; no findings target them (e.g. `spec.md` when the plan is under review).
- **--out** — where to write the report.
- **--mcp** — comma list of MCP servers to require (e.g. `context7,linear,github`). Tooling the user names in prose counts the same as a flag.
- **--skill** — comma list of project skills to require. Tooling the user names in prose counts the same as a flag.
- **--instances N** / **--split a,b,c** / **--single** — override fan-out (see step 3).

Before moving on:
- Echo every `--token` outside {context, out, mcp, skill, instances, split, single} back to the user as unrecognised, and proceed without it.
- For each user-named skill/MCP you cannot find in this session's skill listing or tool discovery, ask the user to correct or drop it; dispatch nothing until they answer.

### 2. Classify

Skim the spec and record four facts — this record is the step's completion criterion, and the last time you read the spec:

1. **Doc-type**, by filename suffix first, then content; the directory never decides it (`docs/plans/` holds both plans and designs):
   - `*-plan.md`, or `## Task N` / `## Phase N` / sequenced steps → **execution plan**
   - `*-design.md`, or `## Decisions` / `## Module Structure` / `## Test Strategy` → **design doc**
   - `*-spec*` / `*-prd*`, or requirements + acceptance-criteria blocks → **spec/PRD**
   - a few lines / one ask → **task card**
   - none resolve → **unclassified**
2. **Line count.**
3. **Touched lenses** — every lens whose "Include when" (step 3) holds.
4. **Tooling signals** — matches against `references/detection-map.md`.

### 3. Decide fan-out

Each lens's surface is its `### <lens>` rubric section in `references/validator-role.md`; the sections are disjoint.

| Lens | Include when |
| --- | --- |
| architecture | doc-type is design doc, execution plan, or unclassified; or the doc names code modules, packages, APIs, or data stores |
| scope | doc-type is spec/PRD, execution plan, or unclassified; or the doc has requirements or acceptance criteria |
| execution | doc-type is execution plan; or the doc mentions phases, milestones, sequencing, dependency ordering, critical path, parallel workstreams, estimates/timeline, rollback, migration, rollout, cutover, feature flags, review gates, or test gates |
| domain | the doc encodes project-specific business rules, workflows, or invariants (not generic CRUD/UI) |
| security | the doc mentions auth, JWS/JWE, KMS, signing, private keys, secrets, credentials, webhook signature verification, access control, injection/attack surface, `process.env`, or tokens/sessions |

Instance count:
- `--single`, a task card, or ≤150 lines → **1 instance**, lens `all`.
- Otherwise → one instance per touched lens (at most 5).
- `--split a,b` replaces the touched-lens set (echo names outside the five as unrecognised). `--instances N` caps the count: when lenses exceed N, merge lenses into N instances, each owning a comma list of lenses. Apply `--split` first, then `--instances`.

Tell the user the doc-type, lens set, and instance count, then continue.

### 4. Resolve tooling per instance

- **Required** — user-named tooling. Assign it to the instance(s) whose lens the detection map lists for it; with no map row, or when that lens isn't dispatched, assign it to every instance. A required tool that fails in a child fails the run (step 5).
- **Optional** — detection-map matches the user didn't name. Assign each to its mapped lens's instance, with the map's Reason. The instance uses it when available and records `unavailable` otherwise.

### 5. Dispatch

Follow `references/dispatch.md`. For each instance, fill `prompts/validator-instance.md` and dispatch a fresh child with the filled prompt and the absolute path of `references/validator-role.md` (a registered `spec-design-validator` already carries the role). Dispatch concurrently within available slots; queue the rest.

A failed child, or one returning a capability failure, gets one retry with a fresh child. If the retry fails, stop: tell the user the lens and the failure, and write no report and no verdict.

The step is complete when every dispatched instance has returned a ledger that meets the prompt's completeness rule. Re-dispatch a ledger that does not; that counts as its retry.

### 6. Synthesize

1. Merge ledgers. Collapse duplicates (same spec lines, same issue): keep the row with repo evidence, else the higher severity.
2. Verdict:
   - any Blocker with `foundational: yes` → **NO-GO**
   - else any Blocker, or any Major with `blocks-start: yes` → **REVISE**
   - else → **GO**; the remaining Majors are its conditions
3. Read `references/report-format.md` and emit the report; it is done when it meets that file's completeness rule.
4. Write it to `--out` when given. Otherwise offer `<spec-dir>/<spec-basename>-validation.md` and write only on acceptance.
