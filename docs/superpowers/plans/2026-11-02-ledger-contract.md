# Validator Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Implement #8 → #11 → #9 as separate changes on one ledger contract.
**Architecture:** The standalone validator role is canonical. Generated validation roles and the loop bundle share its contract and schema.
**Tech Stack:** Markdown instructions, JSON Schema, Python stdlib distribution builder and structural unittest suite.
**Spec:** docs/superpowers/specs/2026-11-02-ledger-contract-design.md

## Global Constraints

Preserve all 26 rubric bullets, five ledger blocks, review authority, verdict rules and agentic-loop's all-severity default. No project check text is executed.

## Review Focus

- Unsupported/conflicting thresholds stop before review.
- Project files cannot authorise themselves or change tool use.
- Project-only lenses survive fan-out overrides.
- Duplicate findings retain every check ID for completeness.
- Isolated skill installs retain schemas and references.

### Task 1: Stable ledger (#8)

**Files:** canonical role, its new references/ledger.schema.json, distribution builder, tests/test_ledger_schema.py, CHANGELOG.md.
**Interfaces:** Produces schema_version 1.0, rubric_version 1, check_id on all review rows and stable rubric IDs.

- [ ] Add failing structural tests for 26 unique IDs, schema fields, severity-specific flags and distribution copies; run unittest discovery and observe missing contract failures.
- [ ] Implement schema, role rows and schema distribution; list every ID in changelog. Rebuild with python3 scripts/build-distribution.py.
- [ ] Run bash scripts/test.sh; expect exit 0. Commit #8 independently.

### Task 2: Authorised project checks (#11)

**Files:** canonical role/schema, validating-specs workflow/instance prompt and project-checks reference, tests/test_ledger_schema.py, CHANGELOG.md.
**Interfaces:** Consumes check_id and adds project.* IDs; produces validated caller-authorised project checks assigned to lenses.

- [ ] Add failing tests for namespace, authority, prompt handoff and coverage; observe failures.
- [ ] Document --project-checks and project_checks task field, validation and trust boundary. Include project lenses before fan-out, reject excluded project checks, preserve all IDs on synthesis. Extend schema namespace and regenerate copies.
- [ ] Run bash scripts/test.sh; expect exit 0. Commit #11 independently.

### Task 3: Minimum severity (#9)

**Files:** canonical role/schema, validating-specs workflow/instance prompt, agentic-loop validation callers, tests/test_ledger_schema.py, CHANGELOG.md.
**Interfaces:** Consumes project-inclusive coverage and adds minimum_severity all|Nit|Minor|Major, Checked status below-threshold.

- [ ] Add failing tests for accepted values, unsupported/conflicting values, suppressed coverage and loop default; observe failures.
- [ ] Add preflight rejection, severity handoff and filter rules; schema reflects threshold and checked status. Pin loop callers to all and regenerate copies.
- [ ] Run bash scripts/test.sh; expect exit 0. Commit #9 independently.
- [ ] Fresh-context review of all changes; fix important findings with regression evidence, run full suite, leave branch ready for user review.
