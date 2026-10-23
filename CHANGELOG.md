# Changelog

All notable changes to the `spec-to-pr` skills suite and plugin are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- The native `team-lead` agent is planning-only: `disallowedTools: Agent,
  NotebookEdit` removes its ability to dispatch subagents, also when it runs as
  the main thread with `claude --agent team-lead`. It returns delegation
  requests for the caller to dispatch.
- The native `code-reviewer` and `spec-design-validator` agents are read-only
  through `disallowedTools`, and now inherit MCP and Skill tools.
- **Breaking:** the `writing-documentation` skill is renamed `diataxis-docs`,
  so it no longer collides with the installed
  `anthropic-skills:writing-documentation`. Invoke it as
  `/spec-to-pr:diataxis-docs` and install it with `--skill diataxis-docs`. Its
  description now leads with docs grounded in the working repository's code.
- The agentic-loop spec planner ends on a basis audit: every choice in §2–§7
  and §10 carries `[source L<n>]`, `[§8 D<n>]`, or `[Q<n> default]`, and the
  spec reviewer audits the tag instead of re-flagging a choice §9 already asks.
  Non-goals go through the two-alternatives test, every §9 question blocks
  planning, and codebase precedent settles only 1:1 library choices.

### Removed

- `diataxis-docs` no longer bundles `references/elements-of-style.md`. Register
  comes from the quadrant file; the LANGUAGE AND STYLE block in `SKILL.md` holds
  the rules shared by every quadrant.
- `diataxis-docs` no longer ships a generated `references/dispatch.md`. Its cut
  pass carries its own instructions for running in a fresh child.

## [0.3.0] - 2026-10-23

### Added

- Independently installable skills for interactive Codex and Claude Code through
  `pnpm dlx skills add`, including individual installation and bundled resources.
- Portable fresh-child role dispatch, with optional native Claude agents and
  explicit failure when required delegation or child tooling is unavailable.
- Interactive run initialization with deterministic source identity, Git
  preflight, exact source snapshots, collision protection, and validated resume.
- Directly callable gate checks, preserving Claude wrapper policy and supporting
  controller-invoked checks in other harnesses.
- Packaging, initialization, and gate tests, plus explicit live-harness
  acceptance requirements. Automated tests alone do not establish full
  interactive compatibility.

### Changed

- Shared roles and validation resources have canonical sources and generated
  distribution copies; the loop no longer requires a sibling validator install.
- Installed Claude hook dependencies travel together with their wrappers.
- Codex uses effective harness model defaults and accurately reports the absence
  of lifecycle interception. Existing headless CI remains Claude-only.

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
