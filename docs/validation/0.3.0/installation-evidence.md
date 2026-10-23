# Skills installation evidence

Recorded 2026-10-23 using `pnpm dlx skills` version **1.7.4**, against a local
snapshot of the proposed 0.3.0 distribution. This verifies local packaging;
the GitHub command cannot install these changes until they are published.

- Discovery returned exactly `agentic-loop`, `validating-specs`, and
  `writing-documentation`.
- Eight isolated project installations passed: suite plus each skill alone,
  in default-link and `--copy` modes, targeting both Codex and Claude Code.
- Every installed file matched its packaged bytes under `.agents/skills` and
  `.claude/skills`, after deleting the installer source snapshot. No sibling
  installation was present in the single-skill cases.
- Initial snapshot counts were 66 loop files, 6 validator files, and 7
  documentation files. The reproducible eval records current counts; these
  counts are evidence, not a fixed package schema.
- No user/global skill installation was modified. Disposable project directories
  are removed by the reproducible eval.

Reproduce after generating the distribution:

```bash
python3 scripts/build-distribution.py
python3 scripts/evals/test_skills_install.py --allow-network
```

The eval is opt-in and has no unittest discovery cases. `--allow-network`
authorizes its `pnpm dlx` dependency resolution. Override `--evidence PATH` to
choose the output transcript; default `/tmp/spec-to-pr-install-evidence.txt`.
The transcript includes exact CLI commands, version, installer output, asset
counts, and pass records. An initial exploratory `--list --json` attempt was
rejected by the CLI; the successful eval uses plain `--list`.

This evidence does **not** establish live interactive skill execution. Complete
fresh-child role/tool use, multi-lens synthesis, question/answer pause and resume,
negative-gate stopping, and full fixture workflows remain separate acceptance
requirements for each harness. Missing live transcripts must remain visible in
release reporting. Headless CI remains Claude-only.
