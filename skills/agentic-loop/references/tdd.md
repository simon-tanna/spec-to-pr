# TDD Iron Law

Every production line in this pipeline is preceded by a failing test. No exceptions without human override.

## Rule

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

If an implementer wrote production code before a test, the work is rejected and restarted. Delete the code. Write the test. Watch it fail. Write minimal code to pass.

## Red-Green-Refactor

1. **RED** — one minimal test for the desired behaviour.
2. **Verify RED** — run it, confirm it fails for the right reason (missing feature, not a typo).
3. **GREEN** — simplest code that passes. No extras.
4. **Verify GREEN** — test passes, no other tests break, output clean.
5. **REFACTOR** — clean up while green. Add no behaviour.

## Test Quality

| Good                                        | Bad                                     |
| ------------------------------------------- | --------------------------------------- |
| Describes the behaviour in its name         | "test1", "it works"                     |
| Uses real code; mocks only when unavoidable | Mocks everything, asserts on mock calls |
| One behaviour per test                      | "and" in the name → split               |

## Common Rationalisations (all rejected)

- "Too simple to test" — takes 30 seconds anyway.
- "I'll test after" — tests written after pass immediately. That proves nothing.
- "I already manually tested" — ad hoc, no record, cannot re-run.
- "Deleting what I have is wasteful" — sunk cost. Rewrite.

## Why Not Just Write Tests After?

Tests-after answer "what does this do?" Tests-first answer "what _should_ this do?" The difference is edge cases discovered vs edge cases remembered. Remembered is always incomplete.

## Enforcement in the Loop

- Plan tasks always start with a test step. Plans that do not are rejected in the plan-review stage.
- Implementer prompts require the test-first sequence.
- One commit per task (see `plan-format.md` Task Granularity Rule), so test + implementation land in the same commit. **The commit body MUST include a `TDD:` line** referencing the failing test (e.g. `TDD: __tests__/bar.test.ts:12-30 written before implementation`). Spec-compliance review verifies (a) the test file is present in the commit diff, (b) the assertions cover the task's `Test contract` bullets, and (c) the `TDD:` line is present. Reviewer trusts the implementer's TDD discipline as recorded — the commit-order check that previously tried to enforce it via git history is removed because atomic per-task commits make it unenforceable.
- **Red→green ordering is verified at implementer runtime and recorded via the `TDD:` trace — it is intentionally NOT auditable from git history.** Because each task is one atomic green commit (bisectability), the test and implementation share a commit and there is no red-then-green pair to inspect. Do not read a single test+impl commit as a TDD violation; the trace is the record.
- **Deterministic backstop:** when the gate hooks are registered, `agentic-loop-check-tdd-trace.sh` (PreToolUse on `tasks.json`) independently confirms — for every task flipped to `status:"done"` with a resolvable `commit_sha` — that the commit diff contains a test path AND the message body carries a `TDD:` line. This turns the otherwise model-only `TDD:` trace into a structural check. It verifies **presence only** (never ordering), matching the atomic-commit design above.
- If the implementer is caught writing code first (no `TDD:` line, or the implementation file appears without a matching test in the same commit), the task restarts. No carry-over of the "reference" code.

## Exceptions

Allowed only with explicit human confirmation:

- Throwaway prototype branches (never merged).
- Generated code (where the generator is tested).
- Pure configuration files.

Everything else: test-first, every time.
