# Portability implementation validation

The 0.3.0 work separates installation compatibility, deterministic helper tests,
and live agent behavior. Installation and offline regressions pass. Full live
interactive acceptance remains incomplete; do not treat this document as release
approval or evidence of an end-to-end Codex run.

## Test-first changes

- Distribution tests first failed because canonical resources and the generator
  were absent. They now verify committed output, detect and repair drift, and
  exercise each skill's resource inventory in an isolated directory.
- Shared-gate tests first failed because the portable CLI did not exist. The
  extracted policies now pass direct-call, installed-wrapper, missing-helper,
  and harness-reporting checks, alongside all 22 original hook scenarios.
- Initializer tests first failed because the helper did not exist. Disposable
  repositories and local bare remotes exercise identity, precedence, source
  snapshots, resume, dirty worktrees, unreachable bases, and branch collisions.
  Independent review added failing regressions for base-branch run-storage
  symlinks and occupied run directories before those cases were fixed.
- PR-body tests caught synthetic run IDs producing invalid `Closes #...` text.
  File/inline runs now omit issue closure and harness-specific authorship;
  numeric legacy CI runs retain their real issue closure.
- Smoke-evaluator tests reject controller-only results and uncorrelated or
  failed child results. They validate trace interpretation, not agent behavior.

Run the offline checks from the repository root:

```bash
bash scripts/test.sh
claude plugin validate .
```

Canonical resources live within the skills. Claude adapter metadata lives in
`adapters/claude/`. After editing canonical resources, run
`python3 scripts/build-distribution.py` and commit the generated outputs.
`--check` reports drift without writing. Installed skills need no build step.

## Installation and live evidence

See [installation-evidence.md](installation-evidence.md) for the actual eight-case
Skills CLI installation matrix and reproducible opt-in evaluator. Both harness
destinations retain every resource after the source snapshot is removed.

See [portable-dispatch-evidence.md](portable-dispatch-evidence.md) for bounded
live CLI attempts, versions, and exact blockers. Remaining acceptance includes
fresh child tool-access evidence, capacity queuing and all-lens collection,
interactive question/answer pause and resume, missing required-tool/role negative
cases, and a complete spec-to-PR fixture in each harness. Existing headless tests
and commit-message `TDD:` checks do not establish those behaviors.
