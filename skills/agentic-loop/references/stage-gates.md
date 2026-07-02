# Stage Transition Gates — Hard Rules

The most common failure mode of past runs has been skipping a stage to "save turns". Do not. The pipeline is not a suggestion — each stage produces an artefact that the next stage depends on. **Every gate below MUST be checked explicitly before `.state` advances.**

## `spec` → `plan`

- **Artefacts:** `spec.md`, `spec-review.md`, `spec-validation.md`
- **Gate:**
  - structured review verdict `approved`
  - `critical=[]`, `important=[]`
  - `spec-validation.md` verdict is `GO` (a `REVISE`/`NO-GO` from `validating-specs` blocks the gate exactly like an `important` finding)
  - `open-questions.md` empty or absent
  - `force_interview === false` on the latest review
  - every `product_decisions_flagged[]` entry has `authorised_by_source === true`

## `plan` → `implement`

- **Artefacts:** `plan.md`, `tasks.json`, `plan-review.md`, `plan-validation.md`
- **Gate:**
  - structured review verdict `approved`
  - `critical=[]`, `important=[]`
  - `plan-validation.md` verdict is `GO`
  - `tasks.json` non-empty
  - every task has at least one test target

## `implement` → `done`

- **Artefacts:** all tasks `done`; per-task `spec_review_sha` AND `quality_review_sha` populated
- **Gate:**
  - resolved quality gates green on full branch
  - final-review verdict `approved`

## Hard gates (enforced by hooks — only when registered)

Four PreToolUse hooks block the most common shortcut paths deterministically — the harness fails the tool call regardless of what the model intends. **This is only true when the hooks are installed and registered** in `.claude/settings.json` (see `setup/SETUP.md` and run `scripts/check-substrate.sh` to verify). If they are not registered, these gates degrade to **model-enforced** — the controller must honour them itself, exactly like the validation verdict below. The hook scripts ship under the skill's `setup/hooks/` and are installed to `.claude/hooks/`:

| Hook                                     | Blocks                                                                                                                                                                                                         |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `agentic-loop-check-tasks-json.sh`       | `Write`/`Edit` to `.agentic-loop/<id>/tasks.json` that marks any task `status:"done"` without both `spec_review_sha` AND `quality_review_sha` populated                                                        |
| `agentic-loop-check-state-transition.sh` | `Write`/`Bash` writes to `.agentic-loop/<id>/.state` setting `plan` without `spec.md` + approved `spec-review.md` (JSON `verdict:"approved"` + `force_interview:false`) + closed `open-questions.md`; setting `implement` without `plan.md` + non-empty `tasks.json` + approved `plan-review.md` + closed `open-questions.md`; or setting `done` while any task is incomplete |
| `agentic-loop-check-pr-ready.sh`         | `Bash` invocations of `gh pr create` while any task is incomplete or `open-questions.md` is non-empty                                                                                                          |
| `agentic-loop-check-tdd-trace.sh`        | `Write`/`Edit` to `.agentic-loop/<id>/tasks.json` marking a task `status:"done"` whose resolvable `commit_sha` lacks a test path in its diff OR a `TDD:` line in its message body (presence check, not ordering) |

If a hook blocks you, do not retry the same call — it will fail again. Read the stderr message, address the underlying gap (run the missing review pass, run the plan loop, close the open questions), then proceed.

**Hook-enforced vs model-enforced gates.** The hooks above enforce the _structured_ gates only — `spec-review.md` verdict + `force_interview`, `tasks.json` shape, `plan-review.md` verdict, `open-questions.md` emptiness, per-task review shas. The `validating-specs` verdict (`spec-validation.md` / `plan-validation.md` must be `GO`) is a **model-enforced** gate, not hook-enforced: `*-validation.md` is `validating-specs`' free-form report, which cannot be statically validated the way the structured JSON can, so no hook greps it. The controller is responsible for honouring the `GO`-only exit in the spec/plan loop. Do not read the "Hard gates" table as a mechanical backstop for the validation verdict — there isn't one; it is on you to check it.
