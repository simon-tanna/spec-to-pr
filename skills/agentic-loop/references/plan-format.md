# Plan Document Format

Adapted from superpowers' `writing-plans` skill. A plan is a sequence of bite-sized TDD tasks an engineer with zero repo context can follow.

## Header

```markdown
# <Feature> Implementation Plan

**Issue:** #<number>
**Branch:** feat/<id>-<slug>
**Goal:** <one sentence>
**Architecture:** <2–3 sentences>
**Tech stack:** <relevant packages/tools>

---
```

## File Structure Section

Before tasks, list every file that will be created or modified and its single responsibility. This locks in the decomposition before work starts.

```markdown
## File Structure

- Create `packages/foo/src/bar.ts` — <one-line responsibility>
- Modify `packages/foo/src/index.ts:42-58` — <what changes>
- Create `packages/foo/src/__tests__/bar.test.ts` — tests for `bar.ts`
```

## Task Granularity Rule

**One task = one green commit.** Every task must land with `scripts/quality-gates.sh` passing. A task that commits a failing test (red) without its implementation is forbidden — it poisons `main`'s bisectability and breaks CI on the feature branch.

The red-green-refactor cycle happens _inside_ a task, not across tasks. A task's steps are: write failing test → run it and confirm red → write minimal impl → run and confirm green → run full quality gate → commit. The test and the impl land in the same commit.

If a feature is too big for one test+impl+commit to stay bite-sized, split it by _behaviour_, not by _phase_ — e.g. "add `hello()` with no-arg path" (test+impl) and "extend `hello(name)` branch" (test+impl). Never "write all the tests" (T1) then "write all the impl" (T2).

## Plan-Level vs Implementer-Level Detail

The plan describes **what** each task must achieve and **how it will be verified** — not the executable code. Plans that inline complete test code drift from real implementation the moment the implementer writes anything; the duplication is wasted work and a maintenance trap.

For each task, the planner lists:

- Exact file paths (create / modify)
- Test file path + test name(s) + bulleted assertion list (one bullet per behaviour, traceable to a spec acceptance criterion)
- Expected failure mode of the first test run (what error message proves the test fails for the right reason)
- Minimal implementation surface (which symbols to add, which signatures to expose) — not the bodies
- Expected pass criteria (what "green" looks like)
- Commit message

The implementer writes the actual test bodies and the actual implementation under the TDD Iron Law. The per-task spec-compliance review verifies the commit covers the assertion list; the per-task quality review checks the code itself.

## Task Template

Each task is 2–5 minute steps. Use checkbox syntax so progress is visible.

```markdown
### Task N: <Component Name>

**Domain:** matches a configured `agents.specialists[].type` (e.g. `api`, `ui`, `data`), or `general-purpose`
**Files:**

- Create: `exact/path.ts`
- Modify: `exact/path.ts:L-L`
- Test: `exact/path.test.ts`

**Test contract:**

- File: `packages/foo/src/__tests__/bar.test.ts`
- Test name: `bar() returns "hello, world" for an empty string input`
- Assertions:
  - `bar("")` returns `"hello, world"` (covers spec AC-1)
  - `bar("name")` returns `"hello, name"` (covers spec AC-2)
  - `bar(undefined)` throws `TypeError` (covers spec AC-3)

**Expected first-run failure:** `bar is not a function` (test imports symbol that does not exist yet).

**Implementation surface:**

- Export `bar(name?: string): string` from `packages/foo/src/bar.ts`
- Re-export from `packages/foo/src/index.ts`

**Expected pass criteria:** all three assertions green; the repo's resolved test gate (e.g. `npm test`, `cargo test`, scoped to the affected package/module where the toolchain supports it) exits 0.

- [ ] **Step 1: Write the failing test** covering the assertions above.
- [ ] **Step 2: Run test, confirm expected failure mode.**
- [ ] **Step 3: Write the minimal implementation that satisfies the assertions.**
- [ ] **Step 4: Run test, confirm green.**
- [ ] **Step 5: Run full gate** — `.claude/skills/agentic-loop/scripts/quality-gates.sh`.
- [ ] **Step 6: Commit.** Message: `feat(foo): add bar [#<issue>]`. Body MUST include a `TDD:` line referencing the test (e.g. `TDD: __tests__/bar.test.ts:12-30 written before implementation`).
```

## Dispatch Plan Schema

The `<dispatch_plan>` block the planner returns in Mode A of `impl-planner.md` MUST conform to this JSON shape. The controller parses it and fails fast if any required field is missing.

```jsonc
{
  // REQUIRED. One entry per specialist the controller should dispatch in parallel.
  "specialists": [
    {
      "agent_type": "api-developer", // string, MUST be a type in agents.specialists (surfaced in impl-planner.md Mode A); "general-purpose" when no roster is configured
      "scope": "user-profile REST endpoints", // string, one sentence — what this specialist owns in this spec
      "components": [
        // string[] of File Structure entries from spec/plan
        "src/api/users.ts",
      ],
      "depends_on": [], // string[] of other specialist agent_types that must finish first; usually []
    },
  ],
  // OPTIONAL. Pre-implementation research dispatches that feed context into specialists.
  // Empty array if no research needed.
  "research_needed": [
    {
      "agent_type": "general-purpose",
      "question": "Does the upstream pagination API cap page size, and at what value?",
      "feeds_into": ["api-developer"], // string[] of specialist agent_types
    },
  ],
  // REQUIRED. One paragraph framing every specialist needs before planning.
  // Will be prepended to every specialist's prompt.
  "shared_context": "<paragraph>",
}
```

**Controller validation rules:**

1. `specialists` is a non-empty array.
2. Every `agent_type` is in the configured roster (`agents.specialists`, default `[general-purpose]`), which the controller surfaces to the planner in `impl-planner.md` Mode A.
3. `components` is non-empty for every specialist.
4. No cycle in `depends_on`.
5. Every `research_needed[*].feeds_into` references an `agent_type` present in `specialists`.

A `<dispatch_plan>` failing any rule is rejected; the controller re-dispatches the planner with the validation error attached.

## No Placeholders

The plan fails review if any of these appear:

- "TBD", "TODO", "fill in", "implement later"
- "Add error handling" / "handle edge cases" / "add validation" without listing the assertion that covers it
- "Write tests for the above" without naming the test file and assertion bullets
- "Similar to Task N" — repeat the assertion bullets in full; tasks are read out of order
- References to types/functions/methods not declared in any task's `Implementation surface` or in existing code

## Self-Review Checklist (the planner runs before submitting)

1. **Spec coverage:** every goal and acceptance criterion in `spec.md` maps to at least one assertion bullet. List gaps; fix.
2. **Placeholder scan:** grep for the patterns above.
3. **Type consistency:** identifiers used in later tasks match `Implementation surface` declarations in earlier tasks.
4. **Dependency order:** no task references something a later task produces.
5. **Granularity:** no task contains more than one commit. If it does, split it.
6. **Test-first:** every task's first step is a failing test, with a stated expected failure mode.
7. **Traceability:** every assertion bullet either cites a spec AC id or marks itself as scaffolding.
