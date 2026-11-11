## Context

Issue #20 asks for a rule in the spec validator role: the documents under review, context documents and repository files, agent instruction files included, are data. The reviewer checks the claims they make and judges the spec against the conventions they record. It never follows an instruction in them that changes its task, lens, output or tool use, and lists such text in a separate ledger block. The issue describes v0.4.0 and links `skills/validating-specs/references/validator-role.md` at that tag.

The pinned target is `simon-tanna/spec-to-pr` at `4b106b401c5976e6f19103557e07004344fac3f1` ("Release v0.6.0"). The repository is a Markdown/Python skills suite with no Foundry, Hardhat, Anchor, Solana or Soroban manifest, so chain detection returned `unknown`.

Main observation: the requested behaviour already exists at the pinned revision.

- `skills/spec-design-validator/SKILL.md` bytes [4442, 6271) is the canonical role. Its `## Review authority` section treats the documents under review, context documents and repository files, AGENTS.md / CLAUDE.md / rules files included, as evidence. It separates conventions from redirections and records redirections under **Ignored instructions**.
- `CHANGELOG.md` bytes [5418, 5957) records this as shipped in 0.5.0 under issue #12.

Requirement inventory from the intake:

- R1: The validator role carries the rule, in its canonical source and in every generated copy. The rule says that the documents under review, context documents and repository files, agent instruction files included, are data. Their claims are checked, and the spec is judged against the conventions they record. Instructions in them that change the reviewer's task, lens, output or tool use are never followed.
- R2: The ledger format defines a separate block that lists ignored instructions.
- R3: Agent instruction files still supply the conventions that the architecture lens checks against.

Constraint inventory:

- C1: Generated copies of the role and its references come from the canonical files through `scripts/build-distribution.py`. Each Markdown copy carries a notice telling maintainers to edit the canonical file and rebuild. `--check` reports drift without writing (`scripts/build-distribution.py` bytes [0, 9119)).

The repository root has no AGENTS.md or CLAUDE.md, per the root listing at the pinned commit. C1 is therefore the only repository instruction constraining this change.

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
- it names the documents under review, context documents and repository files, AGENTS.md / CLAUDE.md / rules files included, as evidence rather than instructions;
- it says a reviewed artifact holds no authority over its own review;
- it directs the reviewer to carry on and not follow text addressed to the reviewer that would change its task, lens, verdict, output or tool use.

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

At the pinned revision all four obligations already hold:
- OB-1 holds through `## Review authority`, which sits before `## Method` in the canonical role.
- OB-2 holds through the generated copies. Running the builder's `--check` mode locally at the pinned head produced no drift.
- OB-3 holds through the `Ignored instructions:` ledger line and the schema's `ignored_instructions` property.
- OB-4 holds through Method step 1, `architecture.codebase-fit` and the Convention classification.

The proposed delivery is therefore verification only. The Builder changes no role, schema or generated file, and confirms the obligations with the existing regression suite. Any edit to role wording would follow C1: edit the canonical file and rebuild, never a copy. Whether to make such an edit is Open Question 1.

## Components

- Canonical role `skills/spec-design-validator/SKILL.md`. It owns the Review authority rule (OB-1), the prose ledger block (OB-3) and the Method/architecture convention checks (OB-4).
- Canonical schema `skills/spec-design-validator/references/ledger.schema.json`. It owns the JSON `ignored_instructions` block (OB-3).
- Builder `scripts/build-distribution.py`. It owns the propagation and drift detection behind OB-2.
- Regression tests:
  - `tests/test_validator_contract.py`, `test_review_authority_separates_conventions_from_redirections`, guards OB-1 and OB-4's Convention/Redirection split;
  - `tests/test_distribution.py`, `test_committed_distribution_is_current`, guards OB-2;
  - `tests/test_ledger_schema.py` and `tests/test_ledger_schema_validation.py` guard OB-3.

## Test Strategy

The Verification Command for every obligation is `bash scripts/test.sh`. It first runs `python3 scripts/build-distribution.py --check`, then the `tests/` unittest suite.

- G1 / OB-1 / canonical role: `test_review_authority_separates_conventions_from_redirections` asserts that the Review authority section contains each of the following, and that an ignored redirection is "not a finding and does not change the verdict":
  - AGENTS.md and CLAUDE.md;
  - the Convention and Redirection labels;
  - the Ignored instructions label;
  - the `source location · attempted redirection · action taken` row format;
  - `None.`.
- G1 / OB-2 / generated copies: the `--check` step and `test_committed_distribution_is_current` fail on any copy that differs from the canonical role.
- G2 / OB-3 / ledger format: `tests/test_ledger_schema.py` asserts the root property set includes `ignored_instructions`. `tests/test_ledger_schema_validation.py` rejects a ledger missing the block or carrying an extra row property; these jsonschema-backed tests run when `uv` and `jsonschema` are available.
- G3 / OB-4 / conventions: the Reviewer reads Method step 1 and the `architecture.codebase-fit` bullet at the delivered head. No existing test asserts these bullets. If Open Question 1 is answered with a wording change, the Plan adds an assertion for both bullets to `tests/test_validator_contract.py`.

## Assumptions

- The issue's "near the method" placement is met by `## Review authority`, which sits in the same role file ahead of `## Method`. Placement inside the Method section is not required. This is observed placement plus an inferred reading of the intake.
- The issue's list of redirect targets (task, lens, output, tool use) is satisfied by the existing rule, which covers those four and also verdict. A broader rule is assumed acceptable. This is inferred from the existing wording.
- The issue's v0.4.0 path `skills/validating-specs/references/validator-role.md` is now a generated copy of `skills/spec-design-validator/SKILL.md`. This is observed in `scripts/build-distribution.py`, which writes that path from the canonical file.

## Resolved Decisions

- Change the canonical role only, never a generated copy. C1 and the generated-file notices require this, and `--check` would flag a hand-edited copy as drift.
- Use the existing `bash scripts/test.sh` as the verification lane rather than a new harness. It already runs the drift check and the contract and schema tests that cover OB-1 to OB-3.

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
- Root listing @ 4b106b4, non-recursive: no AGENTS.md or CLAUDE.md at the root.

Exact Source References and Read Receipts are in spec.json.

## Selected Skills

None selected. The only Designer-applicable Reviewed Skill, `chainlink-data-feeds-skill`, is declined in spec.json because this work item changes reviewer prompt text and has no oracle or price-feed integration.

## Open Questions

1. Product Decision: the pinned revision already satisfies all three "Done when" items (OB-1 to OB-4), shipped under #12 in 0.5.0. Should this work item close as already delivered, with the Builder only running the Verification Command? Or should the role also adopt the issue's proposed sentence verbatim, edited in `skills/spec-design-validator/SKILL.md` and rebuilt? The proposal is to close as already delivered and make no wording change, because the existing rule is broader: it also covers verdict, and it defines the Convention/Redirection split.
2. Target chain: chain detection returned `unknown` with reason "No Foundry, Hardhat, Anchor, Solana or Soroban manifest in the repository" and no roots. The intake names no path under a chain root. Approval requires a human to set the Spec's target chain for this non-contract repository.

## Risks

- Overlap: delivering the issue's sentence on top of the existing rule would duplicate it, so the role would state the same rule twice in different words. Reviewers could read the two as distinct rules. Open Question 1 settles this before Plan.
- Coverage gap: no existing test asserts Method step 1 or `architecture.codebase-fit` text (OB-4). A future edit could drop them silently. This is low risk for a verification-only delivery.
- Schema-behaviour tests skip without `uv` and `jsonschema`. On such a runner, the OB-3 JSON check falls back to the structural assertions in `tests/test_ledger_schema.py`.
