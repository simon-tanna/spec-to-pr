# Changelog

All notable changes to the `spec-to-pr` plugin are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-08-18

### Changed

- **`writing-documentation` now follows Diátaxis structurally, not just in name.**
  The four quadrants were a four-line taxonomy with no way to choose between them
  and no rule against mixing them; the skill's weight sat almost entirely on prose
  register. Added:
  - **The compass** — the two-axis test (action/cognition, acquisition/application)
    that places a document in exactly one quadrant. Choosing the quadrant is now a
    workflow step the skill performs, not a clarification it asks the user for.
  - **Purity** — one quadrant per document, enforced by a completion criterion and
    an explicit re-read pass over each finished draft.
  - **Document sets** — one request may yield several documents (a how-to *and* a
    reference). The set, its quadrants, titles, and paths are proposed at a single
    approval gate before any prose is written.
  - **Per-quadrant craft files** — one per quadrant under `references/`, each
    carrying that quadrant's craft rules, register, title shape, and completion
    bound. Loaded per document written.
  - **An improve branch** — the description always promised it; now the workflow has
    it. Audits an existing doc set exhaustively (quadrant per document, every mixed
    section named, technical claims grounded), proposes an ordered move list, then
    applies the moves one at a time.
  - **Document placement** — the skill now owns the title convention and file path,
    mirroring wherever the repo already keeps docs. It does not scaffold empty
    quadrant directories.

- **Register is now per-quadrant, partly reversing 0.1.3.** Telegraphic prose
  remains the register for **Reference** and **How-to**; **Tutorial** and
  **Explanation** are written in plain, economical prose, because telegraphic
  strips the connective tissue a lesson and a discussion depend on. `SKILL.md`
  keeps only the register-neutral shared rules and the `elements-of-style.md`
  pointer; the quadrant file is the single authority on register.

## [0.1.3] - 2026-08-18

### Changed

- **`writing-documentation` register** — the skill now writes **telegraphic**
  prose: extremely concise, grammar sacrificed for concision, uniformly across
  all four Diátaxis quadrants. The rule outranks
  `references/elements-of-style.md`, which now applies only to what survives the
  cut, and the copyedit subagent cuts before it copyedits. Step 4 gained a
  matching completion bound: a line that could still lose a word has not passed.

## [0.1.2] - 2026-07-03

### Fixed

- **Duplicate hooks load error** — removed the redundant `"hooks":
  "./hooks/hooks.json"` field from `plugin.json`. Current Claude Code loads the
  standard `hooks/hooks.json` automatically, so the explicit manifest reference
  to the same path caused a "Duplicate hooks file detected" failure on install.
  `manifest.hooks` is now reserved for *additional* hook files only.

## [0.1.1] - 2026-07-03

### Added

- **Invocation arguments** — steer a single run's tooling with `--skill a,b`,
  `--mcp x,y`, and (`agentic-loop` only) `--subagent t1,t2`. The headless/CI
  equivalent is the `required: { skills, mcps }` block in
  `.agentic-loop.config.json`. A run's `--skill`/`--mcp` are forwarded to the
  `validating-specs` spec and plan gates. See
  `skills/agentic-loop/references/invocation-args.md`.

## [0.1.0]

### Added
- Initial consolidation of the toolkit into a single plugin.
- **Skills**
  - `agentic-loop` — autonomous spec → PR pipeline (planning, spec/plan
    validation gates, TDD execution loop, review loops, PR creation).
  - `validating-specs` — dispatches the `spec-design-validator` agent to
    pressure-test specs, designs, and plans before implementation.
  - `writing-documentation` — Diátaxis-framework technical documentation.
- **Agents**
  - `spec-design-validator` — brutal spec/design/plan validator.
  - `team-lead` — orchestrator that decomposes work and produces technical
    design documents.
  - `code-reviewer` — quality/correctness/security/comment-quality gate.
- **Hooks** (per-repo opt-in, installed via the agentic-loop skill's `setup/`):
  gate hooks for the loop state machine plus defensive-security guardrails
  (block destructive git, block env/secret reads, block secret exfil,
  block TypeScript violations) and a CI skill-forcing hook.

[0.2.0]: https://github.com/simon-tanna/spec-to-pr/releases/tag/v0.2.0
[0.1.3]: https://github.com/simon-tanna/spec-to-pr/releases/tag/v0.1.3
[0.1.2]: https://github.com/simon-tanna/spec-to-pr/releases/tag/v0.1.2
[0.1.1]: https://github.com/simon-tanna/spec-to-pr/releases/tag/v0.1.1
[0.1.0]: https://github.com/simon-tanna/spec-to-pr/releases/tag/v0.1.0
