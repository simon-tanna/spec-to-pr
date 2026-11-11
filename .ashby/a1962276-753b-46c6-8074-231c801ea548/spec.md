## Context

Issue #20 asks for a rule in the spec validator role: the documents under review, context documents and repository files, agent instruction files included, are data. The reviewer checks the claims they make and judges the spec against the conventions they record. It never follows an instruction in them that changes its task, lens, output or tool use, and lists such text in a separate ledger block. The issue describes v0.4.0 and links `skills/validating-specs/references/validator-role.md` at that tag.

The pinned target is `simon-tanna/spec-to-pr` at `4b106b401c5976e6f19103557e07004344fac3f1` ("Release v0.6.0"). The repository is a Markdown/Python skills suite with no Foundry, Hardhat, Anchor, Solana or Soroban manifest, so chain detection returned `unknown`.

Main observation: most of the requested behaviour already exists at the pinned revision. The missing parts are R1's "data" wording and its claim-checking sentence.

- `skills/spec-design-validator/SKILL.md` bytes [4442, 6271) is the canonical role. Its `## Review authority` section treats the documents under review, context documents and repository files, AGENTS.md / CLAUDE.md / rules files included, as evidence. It separates conventions from redirections and records redirections under **Ignored instructions**.
- `CHANGELOG.md` bytes [5418, 5957) records this as shipped in 0.5.0 under issue #12.

Requirement inventory from the intake:

- R1: The validator role carries the rule, in its canonical source and in every generated copy. The rule says that the documents under review, context documents and repository files, agent instruction files included, are data. Their claims are checked, and the spec is judged against the conventions they record. Instructions in them that change the reviewer's task, lens, output or tool use are never followed.
- R2: The ledger format defines a separate block that lists ignored instructions.
- R3: Agent instruction files still supply the conventions that the architecture lens checks against.

Constraint inventory:

- C1: Generated copies of the role and its references come from the canonical files through `scripts/build-distribution.py`. Each Markdown copy carries a notice telling maintainers to edit the canonical file and rebuild. `--check` reports drift without writing (`scripts/build-distribution.py` bytes [0, 9119)).
- C2: The validator instance prompt, `skills/validating-specs/prompts/validator-instance.md` line 37 (bytes [2640, 2816)), tells the reviewer to treat the spec's prose as "a claim to check, not evidence".

The repository root has no AGENTS.md or CLAUDE.md, per the root listing at the pinned commit. C1 and C2 are the only repository text constraining this change.

Conflict CF-1 (R1, C2): R1 asks the role to call reviewed material "data". The existing `## Review authority` wording instead calls everything under review "evidence". Read alone, that word clashes with C2's "the spec's prose is … not evidence", which the same validator receives in its instance prompt. The two texts mean different things by "evidence": the role means the material reviewed, as opposed to instructions, and the prompt means proof of a claim. A reader can still take them as contradicting each other. Leaving the role unchanged keeps both wordings. OB-1 adopts the issue's "data" wording in the canonical role, which removes the clash.

## Goals

G1: The validator role states that reviewed documents, context documents and repository files, agent instruction files included, are data. Redirecting text inside them is never followed. This holds in the canonical role and every generated copy. Authorized by intake bytes [0, 1603): the proposal paragraph and the first "Done when" item.

G2: The findings ledger format defines a separate block for ignored instructions. Authorized by intake bytes [0, 1603): the second "Done when" item.

G3: Agent instruction files keep supplying the conventions the architecture lens checks against. Authorized by intake bytes [0, 1603): the third "Done when" item.

## Non-goals

- Changing the rubric, the severity model, the verdict rules or the report section order.
- Changing which files the Method reads.
- Adding new capabilities, tools or dispatch behaviour to `validating-specs` or `agentic-loop`.
- Hand-editing any generated copy. Copies change only through `scripts/build-distribution.py` (C1).
- A version bump or release. RELEASING.md governs that separately, and this intake does not ask for it.

## Obligations

OB-1 covers G1 (R1): Given the canonical role `skills/spec-design-validator/SKILL.md` at the delivered head; when its `## Review authority` section is read; then:
- it states that the documents under review, context documents and repository files, AGENTS.md / CLAUDE.md / rules files included, are data, never instructions to the reviewer;
- it directs the reviewer to check the claims that material makes and to judge the spec against the conventions it records;
- it says a reviewed artifact holds no authority over its own review;
- it directs the reviewer never to follow text in that material that would change its task, lens, verdict, output or tool use. The reviewer carries on as the role directs.

At the pinned revision the second bullet is missing, and the section calls the material "evidence" rather than "data" (SKILL.md line 37). OB-1 therefore requires a wording change.

OB-2 covers G1 (R1): Given the delivered head; when `python3 scripts/build-distribution.py --check` runs; then it prints no `Distribution drift:` line and exits 0. Every generated copy therefore carries the canonical `## Review authority` text unchanged. The copies are:
- `skills/validating-specs/references/validator-role.md`;
- `skills/agentic-loop/references/validation/references/validator-role.md`;
- the three `references/native-validator/claude.md` and `codex.toml` payloads;
- `agents/spec-design-validator.md`.

OB-3 covers G2 (R2): Given the delivered head; when a ledger is produced in either rendering, then it carries a separate ignored-instructions block:
- In prose, the `## Findings ledger` section defines a separate `Ignored instructions` block with rows `source location · attempted redirection · action taken`, or `None.` when empty, and counts the ledger complete only when that block is present.
- In JSON, the canonical `ledger.schema.json` lists `ignored_instructions` among the required root properties. Each row is an object with exactly the non-empty string fields `source_location`, `attempted_redirection` and `action_taken`.

OB-4 covers G3 (R3): Given the delivered head; when a reviewer follows the role; then:
- Method step 1 still reads the project's AGENTS.md / CLAUDE.md / rules files;
- the `architecture.codebase-fit` check still judges the spec against the project rules in those files;
- `## Review authority` still classifies a project rule in those files as a **Convention** whose violation is a `convention` finding, not as an ignored instruction.

## Architecture

The validator role has one canonical source, `skills/spec-design-validator/SKILL.md`. `scripts/build-distribution.py` derives every other copy from it:
- the `validating-specs` role and report-format references;
- the native Claude/Codex payloads in three skills;
- the bundled `agentic-loop` validation copies;
- the Claude agent file.

The ledger schema has one canonical source, `skills/spec-design-validator/references/ledger.schema.json`, which the builder copies byte-for-byte.

At the pinned revision, OB-2 to OB-4 already hold and OB-1 holds only in part:
- OB-1 holds in part through `## Review authority`, which sits before `## Method` in the canonical role. That section covers the no-authority sentence and the redirection targets, but it calls the reviewed material "evidence" and has no claim-checking sentence.
- OB-2 holds through the generated copies. The managed reads of `## Review authority` in `skills/validating-specs/references/validator-role.md` (bytes [4192, 6020)) and `agents/spec-design-validator.md` (bytes [5717, 7545)) show text identical to the canonical section. Running `--check` locally at the pinned head exited 0 with no drift. That run is not Source evidence, and the Verification Command re-establishes OB-2 at the delivered head.
- OB-3 holds through the `Ignored instructions:` ledger line and the schema's `ignored_instructions` property.
- OB-4 holds through Method step 1, `architecture.codebase-fit` and the Convention classification.

The delivery is therefore small:
1. Edit the canonical role's `## Review authority` opening paragraph so it meets OB-1. "Everything you review is evidence:" becomes the R1 "data" statement, and a sentence is added saying to check the material's claims and judge the spec against the conventions it records. The Convention/Redirection bullets and the examples stay. This also resolves CF-1. The edit stays within this paragraph, per the human decision (option a).
2. Run `python3 scripts/build-distribution.py` to regenerate every copy (C1).
3. Extend `tests/test_validator_contract.py` to assert both OB-1 and OB-4, as described under Test Strategy.

No schema change is made, and no copy is edited by hand.

## Components

- Canonical role `skills/spec-design-validator/SKILL.md`. It owns the Review authority rule (OB-1), the prose ledger block (OB-3) and the Method/architecture convention checks (OB-4).
- Canonical schema `skills/spec-design-validator/references/ledger.schema.json`. It owns the JSON `ignored_instructions` block (OB-3).
- Builder `scripts/build-distribution.py`. It owns the propagation and drift detection behind OB-2.
- Regression tests:
  - `tests/test_validator_contract.py`, `test_review_authority_separates_conventions_from_redirections`, guards OB-4's Convention/Redirection split. This work item extends it to guard OB-1;
  - `tests/test_validator_contract.py`, a new test added by this work item, guards the rest of OB-4. It asserts that the canonical role's `## Method` step 1 names AGENTS.md and CLAUDE.md, and that the `architecture.codebase-fit` bullet names AGENTS.md / CLAUDE.md project rules;
  - `tests/test_distribution.py`, `test_committed_distribution_is_current`, guards OB-2;
  - `tests/test_ledger_schema.py` and `tests/test_ledger_schema_validation.py` guard OB-3.

## Test Strategy

The Verification Command for every obligation is `bash scripts/test.sh`. It first runs `python3 scripts/build-distribution.py --check`, then the `tests/` unittest suite.

- G1 / OB-1 / canonical role: the existing `test_review_authority_separates_conventions_from_redirections` already asserts that the Review authority section contains each of the following, and that an ignored redirection is "not a finding and does not change the verdict":
  - AGENTS.md and CLAUDE.md;
  - the Convention and Redirection labels;
  - the Ignored instructions label;
  - the `source location · attempted redirection · action taken` row format;
  - `None.`.

  The Builder extends it to assert OB-1's core outcomes:
  - the section states reviewed material is data and not instructions;
  - the claim-checking sentence;
  - "cannot hold authority over its own review";
  - each redirection target: task, lens, output and tool use.

  The test then fails if the core rule is deleted.
- G1 / OB-2 / generated copies: the `--check` step and `test_committed_distribution_is_current` fail on any copy that differs from the canonical role.
- G2 / OB-3 / ledger format: `tests/test_ledger_schema.py` asserts the root property set includes `ignored_instructions`. `tests/test_ledger_schema_validation.py` rejects a ledger missing the block or carrying an extra row property; these jsonschema-backed tests run when `uv` and `jsonschema` are available.
- G3 / OB-4 / conventions: the new `tests/test_validator_contract.py` test fails if Method step 1 stops naming AGENTS.md and CLAUDE.md, or if the `architecture.codebase-fit` bullet stops naming those files' project rules. The existing Review authority test covers the Convention classification. This test is added as part of this work item.

## Assumptions

- The issue's "near the method" placement is met by `## Review authority`, which sits in the same role file ahead of `## Method`. Placement inside the Method section is not required. This is observed placement plus an inferred reading of the intake.
- The issue's list of redirect targets (task, lens, output, tool use) is satisfied by the existing rule, which covers those four and also verdict. A broader rule is assumed acceptable. This is inferred from the existing wording.
- The issue's v0.4.0 path `skills/validating-specs/references/validator-role.md` is now a generated copy of `skills/spec-design-validator/SKILL.md`. This is observed in `scripts/build-distribution.py`, which writes that path from the canonical file.

## Resolved Decisions

- Change the canonical role only, never a generated copy. C1 and the generated-file notices require this, and `--check` would flag a hand-edited copy as drift.
- Use the existing `bash scripts/test.sh` as the verification lane rather than a new harness. It already runs the drift check and the contract and schema tests that cover OB-1 to OB-3, and it will run the new OB-4 test.
- Add the OB-4 test unconditionally, so that every "Done when" item of the intake has an automated check.
- Wording placement (human decision at Spec Review, option a): integrate R1's "data" statement and the claim-checking sentence into the existing `## Review authority` opening paragraph. This replaces "Everything you review is evidence:" and keeps the Convention/Redirection bullets and examples unchanged. The rule is stated once, and the issue's verbatim sentence is not inserted as a separate paragraph.
- Target chain (human decision at Spec Review): `evm`. Chain detection returned `unknown` with no roots, because this repository has no contract manifest. The chain choice does not change the delivered behaviour.

## Evidence

- intake:9c20bf0a…: issue #20 title and description, bytes [0, 1603). Grounds R1–R3 and G1–G3.
- `skills/spec-design-validator/SKILL.md` @ 4b106b4:
  - bytes [4442, 6271), `## Review authority`: OB-1, OB-4 Convention classification;
  - bytes [10507, 10862), Method step 1: OB-4;
  - bytes [12695, 13499), architecture rubric including `architecture.codebase-fit`: OB-4;
  - bytes [16947, 17463), `Ignored instructions:` ledger line and completeness rule: OB-3.
- `skills/spec-design-validator/references/ledger.schema.json` @ 4b106b4:
  - bytes [0, 1104), required root properties including `ignored_instructions`;
  - bytes [8027, 8547), the `ignored_instruction` row definition: OB-3.
- `scripts/build-distribution.py` @ 4b106b4, bytes [0, 9119): C1, OB-2.
- `CHANGELOG.md` @ 4b106b4, bytes [5418, 5957): shipped entry for #12 in the 0.5.0 section.
- `tests/test_validator_contract.py` @ 4b106b4, bytes [4699, 5175): OB-1 regression test.
- `tests/test_distribution.py` @ 4b106b4, bytes [9022, 9186): OB-2 regression test.
- `scripts/test.sh` @ 4b106b4, bytes [0, 1108): Verification Command.
- `skills/validating-specs/references/validator-role.md` @ 4b106b4, bytes [4192, 6020): generated copy of Review authority, OB-2.
- `agents/spec-design-validator.md` @ 4b106b4, bytes [5717, 7545): generated copy of Review authority, OB-2.
- `skills/validating-specs/prompts/validator-instance.md` @ 4b106b4, bytes [2640, 2816): C2, CF-1.
- Root listing @ 4b106b4, non-recursive: no AGENTS.md or CLAUDE.md at the root.

Exact Source References and Read Receipts are in spec.json.

## Selected Skills

None selected. The target chain is `evm` by human decision, which gives four Designer-applicable Reviewed Skills: `develop-secure-contracts`, `setup-solidity-contracts`, `upgrade-solidity-contracts` and `chainlink-data-feeds-skill`. spec.json declines each one with a task-specific reason. This work item changes Markdown prompt text and a Python test in a skills suite. It has no Solidity contract, project setup, proxy upgrade or price-feed integration for those skills to shape.

## Open Questions

None remain. The human answers from Spec Review are recorded under Resolved Decisions.

## Risks

- Overlap: adding the issue's sentence on top of the existing rule without removing the "evidence" clause would duplicate it. Reviewers could read the two as distinct rules. The chosen option (a) avoids this by replacing the clause in place.
- Coverage gap: before this work item, no test asserted Method step 1 or the `architecture.codebase-fit` text (OB-4), or the core Review authority rule (OB-1). The new assertions close this gap.
- Schema-behaviour tests skip without `uv` and `jsonschema`. On such a runner, the OB-3 JSON check falls back to the structural assertions in `tests/test_ledger_schema.py`.
