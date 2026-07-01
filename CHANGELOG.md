# Changelog

All notable changes to the `spec-to-pr` plugin are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

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

[0.1.0]: https://github.com/simon-tanna-dev/agent-loop-plugin/releases/tag/v0.1.0
