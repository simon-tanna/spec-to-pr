# Validator Instance Prompt Template

Fill this template and send it as the `prompt` to each `Agent` call with
`subagent_type: "spec-design-validator"`. Substitute every `{{…}}`. The `{{#if}}` /
`{{#each}}` blocks are authoring guidance — there is **no** template engine. Expand them by
hand: keep the branch that applies, drop the other, and inline one bullet per skill/MCP.

For a **single-instance** run, set `{{LENS}}` to `all domains`, drop the "stay in
your lane" / sibling-validator lines, and soften the closing line to "consumed by a
controller that writes the single human-facing report" (there are no siblings to merge).

---

```
You are validating a spec. Read it end-to-end first:
{{SPEC_ABS_PATHS}}

YOUR SCOPE FOR THIS RUN — restrict ALL findings to: {{LENS}} ({{LENS_DESCRIPTION}}).
{{#if multi_instance}}
Do NOT evaluate other surfaces — sibling validator instances own {{OTHER_LENSES}}.
Stay strictly in your lane so we get deep, non-overlapping coverage.
{{/if}}

Ground every finding in the actual repo: verify claims with Read/Grep/Glob and cite
`file:line`. Do not trust the spec's prose. Apply your standard fatal-flaw hypothesis and
anti-sycophancy protocols. Consult and update your project agent memory as usual.

REQUIRED TOOLING — you MUST use each of these before delivering your verdict:
{{#each REQUIRED_SKILLS}}
- Skill tool: invoke `{{name}}` — {{reason}}. Do not reason about this from memory.
{{/each}}
{{#each REQUIRED_MCPS}}
- {{name}} MCP: FIRST load its schema with
  `ToolSearch` query "{{toolsearch_query}}"
  (you cannot call an mcp__ tool until its schema is loaded), THEN use it to {{reason}}.
  Query the narrowest topic that settles the specific claim in doubt — do not pull broad
  overviews. Cite the doc/result.
{{/each}}

{{#if FOCUS_PROMPTS}}
Pressure-test these specific points (each must end with a severity + concrete fix):
{{FOCUS_PROMPTS}}
{{/if}}

Apply your full rubric and fatal-flaw / anti-sycophancy protocols while hunting, but
deliver a FINDINGS LEDGER only — NOT the narrative 10-section report. For each finding emit:
`severity (Blocker | Major | Minor | Nit) · lens ({{LENS}}) · spec line(s) · repo file:line · issue · concrete fix`.
Confine every finding to the {{LENS}} surface only. Skip the prose sections (Executive
Summary, framing, per-instance verdict) — the controller synthesizes the single
human-facing report and derives the overall verdict from your ledger. Your output is
consumed by a controller that merges it with sibling instances — do not address the human.
```

---

## Filling notes

- `{{LENS}}` / `{{LENS_DESCRIPTION}}` — one of the five canonical lenses from SKILL.md
  step 3, or `all domains` for single-instance:
  - `architecture` — codebase fit, component boundaries, package/monorepo conventions, data flow
  - `domain` — project-specific semantics (your core business rules, workflows, invariants, auth model)
  - `scope` — requirements, scope boundaries, acceptance criteria, test-plan coverage
  - `execution` — dependency ordering, critical path, parallelizable workstreams, estimate realism, rollback/migration, rollout & review/test gates
  - `security` — auth, signing/KMS/JWS, secrets, webhook verification, injection/attack surface
- `{{OTHER_LENSES}}` — the lenses the _other_ dispatched instances own (for disjointness).
- `{{REQUIRED_SKILLS}}` / `{{REQUIRED_MCPS}}` — resolved in SKILL.md step 4 (user flags +
  detection-map auto-detect). Each carries the _reason_ it's needed.
- `{{toolsearch_query}}` — the exact `ToolSearch` selector, e.g.
  `select:mcp__plugin_context7_context7__resolve-library-id,mcp__plugin_context7_context7__query-docs`
  or a keyword form like `context7 library docs`.
- `{{FOCUS_PROMPTS}}` — OPTIONAL. Only include concrete checkpoints you derived from a
  _quick skim_ for classification. Do NOT pre-solve the validation; a few anchoring
  pointers are fine, a full findings list is not (that's the instance's job).
