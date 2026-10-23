# Plan Loop (Stage 2)

**Goal:** a single `plan.md` of bite-sized TDD tasks with exact file paths, test signatures plus assertion bullets (not executable code), and verification steps.

**Entry:** `.state == plan`: the `spec` → `plan` gate in `stage-gates.md` held, `spec.md` is locked and committed, and the feature branch is checked out. Read `plan-format.md` when writing or validating `plan.md`.

Stage 2 runs regardless of how trivial the task looks: a one-line change still gets a one-task plan, a plan review and a per-task TDD cycle.

## Roster

The roster is the immutable `run-requirements.json.specialists` resolved at ingest, including any `--subagent` replacement. Do not reread config on resume. An example roster; substitute the resolved run roster:

| Specialist          | Owns                                                |
| ------------------- | --------------------------------------------------- |
| `api-developer`     | server APIs, services, persistence, auth            |
| `ui-developer`      | UI components, routing, client state                |
| `data-engineer`     | schemas, migrations, pipelines                      |
| `general-purpose`   | anything without a dedicated specialist             |
| the configured reviewer (`agents.reviewer`) | review passes only — never writes plans |

**The controller dispatches every specialist; children do not dispatch children.** Each dispatch uses `dispatch.md`.

## Steps

1. **Dispatch plan.** Dispatch a fresh configured planner child with `prompts/impl-planner.md` (Mode A), `spec.md` and `model: "sonnet"`. Fill its `<roster>` block from `run-requirements.json.specialists`; `invocation-args.md` covers the bare-type → `{type, owns}` adaptation, including the multi-type `owns:"code (planner allocates)"` placeholder. The planner reads `spec.md`, decides which specialists own which components, and returns a `<dispatch_plan>` block conforming to the **Dispatch Plan Schema** in `plan-format.md`; it stops there. Validate the JSON: `specialists` non-empty, every `agent_type` in the roster, no cycles in `depends_on`, every `research_needed[*].feeds_into` naming a known specialist. On a validation failure, re-dispatch the planner with the error. Done when the `<dispatch_plan>` passes every check.
2. **Dispatch specialists.** Dispatch the `research_needed` agents first (sequentially or in parallel, per their `feeds_into` dependencies), then the `specialists` **in parallel**, queued within available child capacity. Prepend `shared_context` to each, and pass:
   - full `spec.md`;
   - the components in their domain, from `<dispatch_plan>`;
   - research findings, when any feed them;
   - `plan-format.md`, with the instruction to return a domain-scoped TDD plan (not a full `plan.md`).

   Prepend the REQUIRED TOOLING block (`invocation-args.md`) built from `run-requirements.json`'s `skills`/`mcps`: each skill to read and apply through the exposed interface with its reason, each MCP with a child-access verification instruction. Dispatch only after confirming the specialist can use the required tooling; the `--mcp` compatibility gate stops unsatisfied required work. Omit `model:` so each specialist inherits its harness default. Done when every specialist has returned its domain plan.
3. **Synthesise.** Dispatch a fresh configured planner child with `prompts/impl-planner.md` (Mode B) and `model: "opus"`, passing `spec.md` and every domain plan inside `<domain_plans>` tags. The planner merges them into one `plan.md` per `plan-format.md`, ordering tasks so that:
   1. cross-domain dependencies are respected (a shared type or API contract exists before a consumer calls it);
   2. within a domain, tasks proceed by increasing integration breadth;
   3. early tasks produce the artefacts later tasks use.

   Task granularity: 2–5 minute steps, exact file paths, test signatures plus assertion bullets, expected failure mode, minimal implementation surface, expected pass criteria, and a commit message with a `TDD:` line. No placeholders and no inline executable test code. The planner runs the Self-Review Checklist from `plan-format.md` before returning.
4. **Extract tasks.** Parse `plan.md` into `tasks.json`, preserving dependency order. Run the shared `tasks` and `tdd` checks on the proposed document (SKILL.md §Shared checks before mutations) before writing it, then run `scripts/git-sync.sh commit "chore(loop): draft plan v<N> for #<issue>"`.

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
5. **Structured review.** Dispatch a fresh configured reviewer carrying the bundled role, with `prompts/decision-rules.md` prepended to `prompts/plan-reviewer.md` and `model: "sonnet"`, on the full plan. In parallel, re-dispatch each domain specialist with `prompts/decision-rules.md` and a sanity-check prompt on their slice (not a re-plan), inheriting harness defaults. Aggregate every verdict into `plan-review.md`, using the same JSON shape as `spec-review.md`.
6. **Adversarial review (when the plan touches a load-bearing decision).** For a plan that touches any *load-bearing decision* (see `prompts/decision-rules.md`; the configured `risk_categories` included), dispatch a second fresh reviewer (`agents.reviewer`) with `prompts/decision-rules.md` prepended to `prompts/plan-reviewer.md`, in adversarial mode, in parallel with step 5. Supply the complete bundled reviewer role and these adversarial instructions, also when a generic native child is used: "Audit this plan for attack-surface and product-risk regressions versus `source.md`. Assume the planner's resolved decisions in `spec.md §8` may be wrong. Flag any change to a load-bearing decision category that is not literally authorised by `source.md`." Merge its findings into `plan-review.md`. Its critical and important findings block `plan` → `implement` exactly like the structured review. This is the gate that catches load-bearing decisions silently resolved against `source.md` (an irreversible operation shipped with no confirmation, an access-control or trust-boundary change, a data-retention reversal) at plan-lock, before any PR exists. Done when the adversarial verdict is in `plan-review.md`, or the plan touches no load-bearing decision.
7. **Validation pass.** Run the bundled `references/validation/workflow.md` inline in this controller (SKILL.md §Spec & Plan Validation), invoked as `<abs plan.md> --context <abs spec.md> --out <abs .agentic-loop/<id>/plan-validation.md>` plus the run's `--skill`/`--mcp` from `run-requirements.json` (never `--subagent`). The report's last line is the verdict: `Verdict: GO`, `Verdict: REVISE` or `Verdict: NO-GO`. Then run `scripts/git-sync.sh commit "chore(loop): plan validation for #<issue>"`.
8. **Loop.** While `plan-review.md` has any `critical` or `important` finding, or the `plan-validation.md` verdict is `REVISE` or `NO-GO`: check the eject flag (SKILL.md §Context hygiene), then return to step 3 with both the structured and adversarial findings and the validation Blockers/Majors. When `plan-review.md` fires the interview gate, run `interview-protocol.md`. Apply §Recurrence cap when it triggers.
9. **Exit** per §Exit.

## Recurrence cap

Apply `spec-loop.md` §Recurrence cap, keyed on `task_id` (or `area` for plan-wide findings); `.state` stays `plan`.

## Replanning Mid-Execute

If Stage 3 surfaces a structural problem (implementer returns `BLOCKED` with a plan-level complaint, or the same spec-compliance issue recurs), jump back to this loop — but only for the affected tasks. Re-dispatch the owning specialist with the failure context, regenerate just those task blocks, update `tasks.json`, review, continue.

## Exit

Exit when the `plan` → `implement` gate in `stage-gates.md` holds. Then:

- Run the shared state check for `implement` and advance `.state` to `implement`.
- Label `state:implementing` (real GitHub issues only).
- Run `scripts/git-sync.sh commit "chore(loop): lock plan for #<issue>"` — commits and pushes `plan.md`, `tasks.json`, `plan-review.md`, `plan-validation.md`, and `.state` together.

Continue with `execution-loop.md`.
