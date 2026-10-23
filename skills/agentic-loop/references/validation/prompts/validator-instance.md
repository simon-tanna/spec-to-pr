<!-- Generated from skills/validating-specs/prompts/validator-instance.md by scripts/build-distribution.py. Maintainers: edit the canonical file and rebuild. -->

# Validator Instance Prompt Template

Fill this template and dispatch it to a fresh child per `../references/dispatch.md`. Substitute every `{{…}}`, including `{{ROLE_ABS_PATH}}`, `{{DOC_TYPE}}`, and `{{CONTEXT_ABS_PATHS}}`. The `{{#if}}` /
`{{#each}}` blocks are authoring guidance — there is **no** template engine. Expand them by
hand: keep the branch that applies, drop the other, and inline one bullet per skill/MCP.

For a **single-instance** run, set `{{LENS}}` to `all` and drop the `multi_instance` block.

---

```
You are a {{LENS}} validator for this {{DOC_TYPE}}. Before anything else, read your role and rubric: {{ROLE_ABS_PATH}} (skip if your system prompt already carries the spec-design-validator role).

Under review — read end-to-end:
{{SPEC_ABS_PATHS}}
{{#if CONTEXT}}
Context only — read as needed; raise no findings against these:
{{CONTEXT_ABS_PATHS}}
{{/if}}

Your lane: the `### {{LENS}}` rubric section(s).
{{#if multi_instance}}
Sibling instances own {{OTHER_LENSES}}; a concern in their surface is theirs — leave it out of your ledger.
{{/if}}

Ground every finding in the repo: verify claims with the available source-reading and search tools and cite `file:line`; the spec's prose is a claim to check, not evidence.

REQUIRED TOOLING — your first actions: run one minimal read-only call per tool to prove access, then use it for its reason. If any required tool is unavailable, return only `CAPABILITY FAILURE: <tool> — <error>`.
{{#each REQUIRED}}
- {{name}} ({{kind: skill|MCP}}) — {{reason}}. Find it via: {{discovery}}.
{{/each}}

OPTIONAL TOOLING — use when available, for its reason; record `unavailable` otherwise.
{{#each OPTIONAL}}
- {{name}} ({{kind}}) — {{reason}}. Find it via: {{discovery}}.
{{/each}}

{{#if FOCUS_PROMPTS}}
Also pressure-test these points:
{{FOCUS_PROMPTS}}
{{/if}}

Deliver a FINDINGS LEDGER (your role's ledger mode) in four blocks:
Tooling evidence: `tool · call made · result` — one line per required and optional tool.
Findings: `severity · kind (flaw | assumption | missing | convention) · lens · spec line(s) · evidence (repo file:line, doc/URL, or spec-internal) · issue · concrete fix`; Blockers append `· foundational: yes|no`, Majors append `· blocks-start: yes|no`.
Strengths: `lens · spec line(s) · evidence · what is strong`.
Checked: `rubric bullet · evidence it holds`.
The ledger is complete when every bullet in your rubric section(s) appears under Findings, Strengths, or Checked, and every listed tool appears under Tooling evidence. Your reader is the controller, which merges ledgers and owns the verdict.
```

---

## Filling notes

- `{{LENS}}` — one lens name, a comma list (merged instances), or `all`.
- `{{DOC_TYPE}}` — the doc-type recorded in the validation workflow's step 2 (Classify).
- `{{ROLE_ABS_PATH}}` — absolute path of `../references/validator-role.md`.
- `{{SPEC_ABS_PATHS}}` / `{{CONTEXT_ABS_PATHS}}` — absolute paths of the documents under review and of the `--context` documents; drop the `CONTEXT` block when there are none.
- `{{OTHER_LENSES}}` — lenses owned by the other dispatched instances.
- `REQUIRED` / `OPTIONAL` — from the validation workflow's step 4 (Resolve tooling); `{{reason}}` comes from the detection-map Reason column, or from the user's words for user-named tooling.
- `{{discovery}}` — how the child finds the tool in its harness (on Claude, a `ToolSearch` keyword query such as `context7 library docs`).
- `{{FOCUS_PROMPTS}}` — optional; only checkpoints from the classification skim, one line each.
