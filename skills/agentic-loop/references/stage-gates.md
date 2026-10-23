# Stage Transition Gates — Hard Rules

The most common failure mode of past runs has been skipping a stage to "save turns". Do not. The pipeline is not a suggestion — each stage produces an artefact that the next stage depends on. **Every gate below MUST be checked explicitly before `.state` advances.**

## `spec` → `plan`

- **Artefacts:** `spec.md`, `spec-review.md`, `spec-validation.md`
- **Gate:**
  - structured review verdict `approved`
  - `critical=[]`, `important=[]`
  - `spec-validation.md` ends on the line `Verdict: GO` (`Verdict: REVISE`/`Verdict: NO-GO` blocks the gate exactly like an `important` finding)
  - `open-questions.md` empty or absent
  - `force_interview === false` on the latest review
  - every `product_decisions_flagged[]` entry has `authorised_by_source === true`

## `plan` → `implement`

- **Artefacts:** `plan.md`, `tasks.json`, `plan-review.md`, `plan-validation.md`
- **Gate:**
  - structured review verdict `approved`
  - `critical=[]`, `important=[]`
  - `plan-validation.md` ends on the line `Verdict: GO`
  - `tasks.json` non-empty
  - every task has at least one test target

## `implement` → PR open

- **Artefacts:** all tasks `done`; per-task `spec_review_sha` AND `quality_review_sha` populated
- **Gate:**
  - resolved quality gates green on full branch
  - final-review verdict `approved`; a `needs-changes` verdict sends every critical and important finding back to Stage 3 as a fix task
- **End state:** `.state` stays `implement` after `gh pr create` succeeds; the merge pipeline owns `state:done`.

## Hard gates (enforced by hooks — only when registered)

Four PreToolUse hooks block the most common shortcut paths deterministically — the harness fails the tool call regardless of what the model intends. **This is only true when the hooks are installed and registered** in `.claude/settings.json` (see `setup/SETUP.md` and run `scripts/check-substrate.sh` to verify). If they are not registered, these gates degrade to **model-enforced** — the controller must honour them itself, exactly like the validation verdict below. The hook scripts ship under the skill's `setup/hooks/` and are installed to `.claude/hooks/`:

| Hook                                     | Blocks                                                                                                                                                                                                         |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `agentic-loop-check-tasks-json.sh`       | `Write`/`Edit` to `.agentic-loop/<id>/tasks.json` that marks any task `status:"done"` without both `spec_review_sha` AND `quality_review_sha` populated                                                        |
| `agentic-loop-check-state-transition.sh` | `Write`/`Bash` writes to `.agentic-loop/<id>/.state` setting `plan` without `spec.md` + approved `spec-review.md` (JSON `verdict:"approved"` + `force_interview:false`) + closed `open-questions.md`; setting `implement` without `plan.md` + non-empty `tasks.json` + approved `plan-review.md` + closed `open-questions.md`; or setting `done` while any task is incomplete (`done` is the merge pipeline's transition) |
| `agentic-loop-check-pr-ready.sh`         | `Bash` invocations of `gh pr create` while any task is incomplete or `open-questions.md` is non-empty                                                                                                          |
| `agentic-loop-check-tdd-trace.sh`        | `Write`/`Edit` to `.agentic-loop/<id>/tasks.json` marking a task `status:"done"` whose resolvable `commit_sha` lacks a test path in its diff OR a `TDD:` line in its message body (presence check, not ordering) |

If a hook blocks you, do not retry the same call — it will fail again. Read the stderr message, address the underlying gap (run the missing review pass, run the plan loop, close the open questions), then proceed.

**Hook-enforced vs model-enforced gates.** The hooks above enforce the _structured_ gates only — `spec-review.md` verdict + `force_interview`, `tasks.json` shape, `plan-review.md` verdict, `open-questions.md` emptiness, per-task review shas. The `validating-specs` verdict is a **model-enforced** gate: no hook reads `*-validation.md`. The controller checks that the report's last line is exactly `Verdict: GO` (match the whole line; `NO-GO` contains `GO`) before advancing the spec/plan loop.

## Portable controller checks

Every harness invokes `scripts/check-gates.sh` before the corresponding state or
task mutation and before PR readiness, using the explicit absolute run directory.
See SKILL.md's shared-check section for CLI examples and proposed-content staging.
The existing Claude wrappers preserve Write versus Edit fragment policies.
Codex uses direct checks and has no lifecycle interception in this release.
A helper result cannot substitute for the behavioral gates above: verify actual
review results, GO verdicts, red-before-green evidence, and successful quality
commands independently. A tool-access failure or missing fresh review stops
progression even if all four machine checks would allow it.
