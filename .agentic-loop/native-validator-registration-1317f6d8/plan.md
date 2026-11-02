# Native Validator Registration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Generate self-contained Claude/Codex validators, explicitly register them safely from each relevant skill, and prefer exposed native selection with bundled fallback.
**Architecture:** Extend the stdlib distribution builder from the unchanged canonical reviewer rubric, keeping plugin and standalone reference mapping separate. Copy one setup implementation and complete payloads into three independently installable skills; update the existing dispatch instructions rather than adding a runtime router.
**Tech Stack:** Python standard library, unittest, Markdown, JSON, TOML, existing offline regression scripts.
**Spec:** [.agentic-loop/native-validator-registration-1317f6d8/spec.md](spec.md)
**Issue:** null (inline run)
**Branch:** feat/native-validator-registration-1317f6d8

## Global Constraints

- Canonical rubric: `skills/spec-design-validator/SKILL.md`; preserve reviewer criteria/output contracts and existing Claude plugin behavior.
- Required setup interface: `python3 <installed-skill>/scripts/setup-validator.py --host claude|codex|both [--project-root <directory>]`; default project root is cwd.
- Setup is explicit, project-only, stdlib-only, self-contained in spec-design-validator, validating-specs, and agentic-loop; no checkout, sibling-skill, or CLAUDE_PLUGIN_ROOT dependency.
- Preflight all destinations; preserve unrelated/local edits; create missing, accept identical, update only ownership-hash-matching managed files; conflicts mean nonzero exit and no planned writes.
- Retain existing Claude model behavior; Codex fields are exactly name, description, developer_instructions; change no models, permissions, sandbox, or MCP configuration.
- Native eligibility depends on this host's exposed selectable spawn schema, never file presence; current Codex spawn lacks an agent-type selector.
- Every task is one green commit; tests precede implementation. Resolved test gate is `bash scripts/test.sh`; controller-only ignored gate configuration is not shipped.
- Ordinary I/O failures require an accurate error and recoverable state, not transactional rollback; explain manual recovery when partial writes conflict on rerun.

## Review Focus

- Local edits at any planned destination stop the whole preflight without mutation — T2 `test_conflicts_preflight_every_destination`.
- Quotes, backslashes, spaces, and Unicode in absolute project paths preserve reference resolution — T2 `test_self_contained_resources_and_escaped_paths`.
- Symlink escapes and unsafe ownership metadata cannot authorize writes outside fixed project destinations — T2 `test_reject_symlink_escape_and_unsafe_metadata`.
- Interrupted writes report failure; reruns either recover safely or identify conflicting paths and actionable preservation/recovery steps — T2 `test_unrelated_files_and_io_failure`.
- Native registration exists but selector is absent, or a started native worker fails: use schema-based fallback only before launch and existing failure policy afterward — T3 named controller tests.

## File Structure

- Modify `scripts/build-distribution.py` — canonical standalone generation, setup copying, output ownership/drift.
- Create `adapters/claude/spec-design-validator-standalone.json` and `adapters/codex/spec-design-validator.json` — separate host wrappers.
- Create `scripts/setup-validator.py` — canonical safe project installer.
- Generate `skills/spec-design-validator/scripts/setup-validator.py`, `skills/validating-specs/scripts/setup-validator.py`, `skills/agentic-loop/scripts/setup-validator.py` — identical independent commands.
- Generate `skills/spec-design-validator/references/native-validator/claude.md`, `skills/spec-design-validator/references/native-validator/codex.toml` — standalone templates.
- Generate `skills/spec-design-validator/references/native-validator/references/ledger.schema.json`, `skills/spec-design-validator/references/native-validator/references/project-checks.md` — reference closure.
- Generate `skills/validating-specs/references/native-validator/claude.md`, `skills/validating-specs/references/native-validator/codex.toml` — standalone templates.
- Generate `skills/validating-specs/references/native-validator/references/ledger.schema.json`, `skills/validating-specs/references/native-validator/references/project-checks.md` — reference closure.
- Generate `skills/agentic-loop/references/native-validator/claude.md`, `skills/agentic-loop/references/native-validator/codex.toml` — standalone templates.
- Generate `skills/agentic-loop/references/native-validator/references/ledger.schema.json`, `skills/agentic-loop/references/native-validator/references/project-checks.md` — reference closure.
- Create `tests/test_native_generation.py`, `tests/test_validator_setup.py`, `tests/test_native_installation.py` — generation, setup, installation/command coverage.
- Modify `tests/test_validator_contract.py` — selector/fallback/failure instruction contracts.
- Modify `scripts/evals/test_skills_install.py` — actual independent installation evaluator.
- Modify `skills/validating-specs/references/dispatch.md` — canonical capability-aware native preference.
- Generate `skills/agentic-loop/references/dispatch.md`, `skills/agentic-loop/references/validation/references/dispatch.md`, `skills/agentic-loop/references/validation/workflow.md` — canonical dependent copies.
- Modify `skills/validating-specs/SKILL.md`, `skills/agentic-loop/setup/SETUP.md`, `README.md`; create `skills/spec-design-validator/setup/SETUP.md` — operational setup guidance outside reviewer rubric.
- Rebuild existing generated plugin/bundled outputs owned by `scripts/build-distribution.py:outputs()` when canonical inputs change; preserve their existing paths and plugin-specific mapping.

## Task 1: Generate standalone adapters and reference payloads

**Domain:** general-purpose. **Dependencies:** none.
**Files:** builder, two adapter JSON files, all twelve native payload files above; test `tests/test_native_generation.py`.
**Interfaces / implementation surface:** retain `outputs() -> dict[Path, str]`; add `standalone_payloads(body: str) -> dict[str, str]` returning claude.md/codex.toml. Use `{{PROJECT_REFERENCES}}` solely in reference-mapping instructions. Generate directly from canonical inputs and prune only owned stale payloads.
**Test contract:** in `tests/test_native_generation.py`:
- `test_host_payloads_preserve_rubric_and_worker_contract`: canonical rubric occurs once unchanged; Claude retains worker rules/model/exclusions and plugin mapping; Codex parses with precisely its three allowed keys. (Goals 1, 3)
- `test_payload_reference_closure_for_each_skill`: all three complete reference payloads; no sibling/source dependency or nested SKILL.md. (Goals 2, 3)
- `test_canonical_changes_propagate_without_intermediates`: temporary canonical rubric/reference edits propagate to plugin and every standalone payload despite absent generated intermediates. (Goal 1)
- `test_native_payload_drift_and_stale_outputs`: changed/missing/orphan outputs fail --check with paths; rebuild restores outputs and removes owned stale files only. (Generation acceptance)
**Expected first-run failure:** missing standalone claude.md path assertion.
**Expected pass criteria:** named tests, existing distribution coverage, offline gate, and distribution --check exit zero.
- [ ] **Step 1:** Write the four failing tests with the assertion contracts above.
- [ ] **Step 2:** Run `python3 -m unittest discover -s tests -p test_native_generation.py -v`; confirm the expected missing-output failure.
- [ ] **Step 3:** Implement the minimal builder/wrappers and run `python3 scripts/build-distribution.py`.
- [ ] **Step 4:** Repeat focused tests; run `python3 scripts/build-distribution.py --check`; confirm green.
- [ ] **Step 5:** Run `bash scripts/test.sh` and `bash /Users/simondev/.codex/plugins/cache/spec-to-pr-marketplace/spec-to-pr/0.5.0/skills/agentic-loop/scripts/quality-gates.sh`; confirm exit zero.
- [ ] **Step 6:** Commit `feat: generate standalone validator adapters`; body includes `TDD: tests/test_native_generation.py written before implementation`.

## Task 2: Ship safe setup in three independently installed skills

**Domain:** general-purpose. **Dependencies:** T1.
**Files:** canonical setup, builder, three generated setup scripts above; test `tests/test_validator_setup.py`.
**Interfaces / implementation surface:** `main(argv: list[str] | None = None) -> int`; `planned_files(skill_root: Path, project_root: Path, host: str) -> dict[Path, bytes]`; `preflight(project_root: Path, planned: dict[Path, bytes]) -> dict[str, str]`; `install(project_root: Path, planned: dict[Path, bytes], statuses: dict[str, str]) -> None`.
Consume T1 templates relative to the installed script. Fixed destinations: `.claude/agents/spec-design-validator.md`, `.codex/agents/spec-design-validator.toml`, `.spec-to-pr/validator/references/ledger.schema.json`, `.spec-to-pr/validator/references/project-checks.md`, `.spec-to-pr/validator/ownership.json`. Manifest records version and allowlisted relative paths/SHA-256 hashes; write metadata last, preserve ownership for unselected hosts. Encode absolute reference paths separately for Markdown/TOML. Copy canonical setup byte-for-byte into three skills.
**Test contract:** in `tests/test_validator_setup.py`:
- `test_required_host_and_project_selection`: missing/invalid host or invalid root fails before writes; all three host options select exact registrations; cwd default and explicit root work. (Goal 2)
- `test_self_contained_resources_and_escaped_paths`: each isolated skill installs after source removal; spaces/quotes/backslashes/Unicode yield valid Markdown/TOML resolving copied absolute references; no unresolved token or CLAUDE_PLUGIN_ROOT. (Goal 3)
- `test_repeat_update_and_move`: created/unchanged/updated reports match writes; repeats do not rewrite; payload upgrades update hash-owned files; project moves refresh paths; one-host then both retains ownership. (Goals 2, 5)
- `test_conflicts_preflight_every_destination`: conflicting contents/types or local modifications list paths, exit nonzero, and leave every planned file/metadata byte-identical; identical unmanaged files may be adopted. (Goal 5)
- `test_reject_symlink_escape_and_unsafe_metadata`: destination/ancestor symlink escapes, malformed metadata/hashes, traversal/absolute/unexpected ownership paths fail without mutation; metadata cannot grant arbitrary writes/deletes. (Project-only scope; Goal 5)
- `test_unrelated_files_and_io_failure`: unrelated agents/config stay identical; injected write failure exits nonzero without success claim; rerun either safely recovers missing/identical/hash-owned content or reports conflicts with instructions to preserve edits, inspect paths, and explicitly restore/remove affected partial managed files before retry. Successful runs include reload/new-session guidance without discovery claims. (Goals 5, 6)
**Expected first-run failure:** installed setup script absent; selected command exits nonzero.
**Expected pass criteria:** all host/skill integration combinations and prior tests pass; conflict snapshots unchanged.
- [ ] **Step 1:** Write the six failing tests with the assertion contracts above.
- [ ] **Step 2:** Run `python3 -m unittest discover -s tests -p test_validator_setup.py -v`; confirm missing-script failure.
- [ ] **Step 3:** Implement setup, builder copying, and rebuild with `python3 scripts/build-distribution.py`.
- [ ] **Step 4:** Repeat setup and generation tests; run `python3 scripts/build-distribution.py --check`; confirm green.
- [ ] **Step 5:** Run `bash scripts/test.sh` and the absolute quality-gates command in T1; confirm exit zero.
- [ ] **Step 6:** Commit `feat: add safe project validator setup`; body includes `TDD: tests/test_validator_setup.py written before implementation`.

## Task 3: Prefer selectable native reviewers and verify installation closure

**Domain:** general-purpose. **Dependencies:** T1, T2.
**Files:** dispatch/copies, README, three setup-guidance files, installer evaluator, `tests/test_validator_contract.py`, `tests/test_native_installation.py` as listed above.
**Interfaces / implementation surface:** update canonical dispatch instructions, rebuild dependent copies; extend existing `scripts/evals/test_skills_install.py:main()` after asset-closure checks. Consume T2's CLI unchanged; add no runtime routing framework. Keep setup instructions outside canonical reviewer rubric.
**Test contract:**
- `tests/test_validator_contract.py:ControllerContractTests.test_native_selection_requires_exposed_selector`: available native role plus selectable schema prefers native; file presence/current Codex schema alone uses fresh bundled generic fallback; explicit generic selections stay generic; unavailable external custom roles retain errors. (Goal 4)
- `tests/test_validator_contract.py:ControllerContractTests.test_native_failure_retains_review_failure_policy`: started native failures retain retry/stop policy without silent fallback; each attempt/lens uses fresh context and retains artifact paths, tooling, lens/output instructions. (Goal 4)
- `tests/test_native_installation.py:test_independent_setup_after_source_removal`: each skill alone, no siblings/source, installs complete selected host/reference closure in offline fixtures; distinguish fixtures from real Skills CLI evidence. (Goals 2, 3)
- `tests/test_native_installation.py:test_documented_commands_match_cli`: execute documented required-host commands for all three skills in temporary roots; cover destinations/conflicts/managed upgrades/moves/recovery/reloads/plugin-versus-standalone/inherited permissions/fallback; rubric excludes setup; no unsupported finding-quality claims. (Goals 2, 6)
- Evaluator acceptance: real default and --copy installations, each skill alone and suite, both host layouts; source removed before setup; validate resources and host syntax; preserve opt-in network and evidence logging. (Installation acceptance)
**Expected first-run failure:** dispatch still mandates standalone generic workers and lacks exposed-selector eligibility.
**Expected pass criteria:** contract/closure/command tests and all regression/drift gates pass; record actual host smoke discovery/spawn separately, with unavailable verification explicitly incomplete.
- [ ] **Step 1:** Write named contract/installation tests before changing instructions/evaluator.
- [ ] **Step 2:** Run `python3 -m unittest discover -s tests -p test_validator_contract.py -v` and `python3 -m unittest discover -s tests -p test_native_installation.py -v`; confirm expected contract failure.
- [ ] **Step 3:** Update canonical instructions, operational guidance, evaluator; run `python3 scripts/build-distribution.py`.
- [ ] **Step 4:** Repeat focused tests and `python3 scripts/build-distribution.py --check`; confirm green.
- [ ] **Step 5:** Run `bash scripts/test.sh` and the absolute quality-gates command in T1; confirm exit zero.
- [ ] **Step 6:** Run `python3 scripts/evals/test_skills_install.py --allow-network --evidence /tmp/native-validator-install-evidence.txt` when networking is available; record actual results and separately record unavailable installation/runtime smoke evidence as incomplete.
- [ ] **Step 7:** Commit `docs: enable native validator dispatch and verify installation closure`; body includes `TDD: tests/test_validator_contract.py and tests/test_native_installation.py written before implementation`.

## Self-Review

Completed: all six goals and acceptance groups map to named tests; all five Review Focus edges are covered; no placeholders or executable test bodies; interfaces and dependencies agree; each task has one green commit, explicit red/green commands, and a TDD commit-body line. No model/permission changes or transactional recovery requirement introduced.
