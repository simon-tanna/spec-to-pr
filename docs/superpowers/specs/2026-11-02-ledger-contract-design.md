# Validator ledger contract

Approved approach: three separate dependent changes, #8 → #11 → #9.

## Intent and constraints

Give callers stable, parseable review coverage without weakening review authority or verdicts. Retain prose rendering, the five ledger blocks, all 26 existing rubric bullets, and agentic-loop's all-severity default. Edit the standalone role as the source of truth and rebuild every distribution. No execution of project check text.

## Approaches

Use JSON Schema plus stable IDs rather than requiring callers to parse prose. For extensions, use caller-authorised files and inline task-prompt checks; inline-only is simpler but forces callers to repeat rules. Automatic repository discovery is unsuitable because reviewed content cannot authorise its own checks. The user approved explicitly authorised files plus inline checks.

## Contract

#8: publish schema version 1.0, retain explicit severity flags, identify every finding, strength and checked row by rubric check ID, and log every introduced ID. Ship schema copies in all three skill distributions.

#11: reserve project.* IDs; authorisation comes only from caller invocation/task prompt. Validate unique IDs, the five lenses and nonempty check text before review. Authorised check files supply declarative criteria, never tool/task/output instructions. Include project lenses in fan-out and project IDs in coverage; preserve multiple check IDs when merging duplicate findings.

#9: --min-severity and task field minimum_severity accept exactly all, Nit, Minor, Major. Absence means all; conflicting or unsupported inputs fail before review. Suppress only Minor/Nit below threshold; record checked status below-threshold with evidence, without exposing issue/fix or claiming success. Blocker/Major findings and verdict rules remain intact. Agentic-loop initially passes all explicitly.

## Builder decisions

Use string file:line locations/evidence, yes/no severity flags, closed schema objects, and a versioned rubric identifier. Keep completeness and cross-row constraints as semantic checks stated beside the schema. Offline tests pin schema and generated resources; live-agent scenarios cover instruction trust and filtering separately.
