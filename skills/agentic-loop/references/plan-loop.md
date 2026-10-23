# Plan Loop — Detailed Protocol

## Entry

`.state` == `plan`. `spec.md` locked and committed. Feature branch checked out.

## Domain Decomposition

The planner reads `spec.md` and identifies which configured specialists own which components. The roster is the immutable `run-requirements.json.specialists` resolved at ingest, including any `--subagent` replacement. Do not reread config on resume. An example roster — substitute the resolved run roster:

| Specialist          | Owns                                                |
| ------------------- | --------------------------------------------------- |
| `api-developer`     | server APIs, services, persistence, auth            |
| `ui-developer`      | UI components, routing, client state                |
| `data-engineer`     | schemas, migrations, pipelines                      |
| `general-purpose`   | anything without a dedicated specialist             |
| the configured reviewer (`agents.reviewer`) | review passes only — never writes plans |

## Parallel Dispatch

**The planner does NOT dispatch specialists directly** — Claude Code does not support subagent nesting. The flow is:

1. **Controller → fresh planner child (impl-planner.md Mode A)** — the planner reads `spec.md` and returns a `<dispatch_plan>` JSON block listing which specialists to dispatch and their component scope. The planner stops here.

2. **Controller dispatches specialists in parallel** — the controller reads `<dispatch_plan>` and spawns one fresh child per specialist using `references/dispatch.md`, queuing work within available capacity. Each specialist receives:
   - Full `spec.md`
   - Scoped subset: the components in their domain (from `<dispatch_plan>`)
   - Plan format from `plan-format.md`
   - Instruction to return a domain-scoped TDD plan file (not a full `plan.md`)

3. **Controller → fresh planner child (impl-planner.md Mode B)** — the controller collects the domain plans and passes them to the planner for synthesis into `plan.md` + `tasks.json`.

Dispatch independent specialists concurrently within available capacity; queue remaining work and collect every required result before synthesis. All dispatch remains controller-owned.

## Synthesis

The planner merges the domain plans into one `plan.md` and orders tasks so:

1. Cross-domain dependencies are respected (e.g. a shared type or API contract exists before a consumer calls it).
2. Within a domain, tasks proceed by increasing integration breadth.
3. Early tasks produce artefacts used by later tasks.

The planner runs the Self-Review Checklist from `plan-format.md` before submitting.

## Task Extraction

Parse `plan.md` into `tasks.json`:

```json
{
  "issue": 42,
  "branch": "feat/42-retry-logic",
  "tasks": [
    {
      "id": "T1",
      "title": "Add retry helper",
      "domain": "backend",
      "file_targets": [
        "packages/foo/src/retry.ts",
        "packages/foo/src/__tests__/retry.test.ts"
      ],
      "deps": [],
      "status": "pending",
      "commit_sha": null,
      "task_start_sha": null,
      "spec_review_sha": null,
      "quality_review_sha": null,
      "blocker_count": 0
    }
  ]
}
```

## Review

Dispatch in parallel, with `prompts/decision-rules.md` prepended to each reviewer prompt:

- `code-reviewer` with `prompts/plan-reviewer.md` on the full plan.
- Each domain specialist with a sanity-check prompt on their slice (not a re-plan).
- **For plans that touch any *load-bearing decision* (see `prompts/decision-rules.md`; the configured `risk_categories` included) — ALSO dispatch the configured reviewer (`agents.reviewer`) in adversarial mode** — prompt: "audit this plan for attack-surface and product-risk regressions versus `source.md`. Assume the planner's resolved decisions in `spec.md §8` may be wrong. Flag any change to a load-bearing decision category that is not literally authorised by `source.md`." Run in parallel with the standard reviewers. (Always supply the complete bundled reviewer role and adversarial stage instructions, including when a generic native child is used.)

Critical findings from the adversarial pass carry the same weight as critical findings from the standard review. Aggregate all verdicts into `plan-review.md` using the same JSON shape as `spec-review.md`. This is the gate that catches load-bearing decisions silently resolved against `source.md` (e.g. an irreversible operation shipped with no confirmation, an access-control or trust-boundary change, a data-retention reversal) — at plan-lock, not after the PR is open.

**Then run the validation pass.** Read and execute the bundled `references/validation/workflow.md` inline in the controller, resolving its resources under `references/validation/` (see SKILL.md `## Spec & Plan Validation`). Pass the explicit `plan.md` path as the document under review plus `spec.md` for context, and direct its merged report to `plan-validation.md`. It returns one `GO | REVISE | NO-GO` verdict; a `REVISE`/`NO-GO` feeds back into the next plan cycle like a `critical`/`important` finding. Commit `plan-validation.md` via `scripts/git-sync.sh commit`.

## Recurring-issue Escalation

Same single trigger as the spec loop: the same `task_id` (or `area` for global findings) appears in `critical` or `important` across two consecutive iterations. On the trigger, post the comment, set label `state:blocked` (or `state:needs-decision` if the recurring finding is attack-surface PRODUCT-class), and exit 0. The loop bounces back to spec, not back into plan-revision.

## Loop Exit

Same exit criteria as the spec loop: `plan-review.md` `verdict=approved`, `critical=[]`, `important=[]`, **AND `plan-validation.md` verdict is `GO`**.

On exit:

- Advance `.state` to `implement`.
- Label `state:implementing`.
- Run `scripts/git-sync.sh commit "chore(loop): lock plan for #<issue>"` — commits and pushes `plan.md`, `tasks.json`, `plan-review.md`, and `.state` together.

## Replanning Mid-Execute

If Stage 3 surfaces a structural problem (implementer returns `BLOCKED` with a plan-level complaint, or the same spec-compliance issue recurs), jump back to this loop — but only for the affected tasks. Re-dispatch the owning specialist with the failure context, regenerate just those task blocks, update `tasks.json`, review, continue.
