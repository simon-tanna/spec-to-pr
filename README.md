# spec-to-pr

An agentic development toolkit for Claude Code. It bundles an autonomous
**spec → PR** loop with the supporting skills and agents it relies on: spec
validation, code review, and documentation.

## What's inside

### Skills

| Skill | What it does |
|-------|--------------|
| **`agentic-loop`** | The flagship pipeline. Takes a spec, task card, or GitHub issue and drives it end-to-end: planning → spec/plan validation gates → TDD execution loop → review loops → PR. Invoke it with "run the agentic loop", "implement this issue", or "take this from spec to PR". |
| **`validating-specs`** | Pressure-tests a spec, design doc, or implementation plan before engineering starts, dispatching the `spec-design-validator` agent. Returns a `GO` / `REVISE` / `NO-GO` verdict. |
| **`writing-documentation`** | Produces structured technical documentation using the [Diátaxis](https://diataxis.fr/) framework (tutorials, how-to guides, reference, explanation). |

### Agents

| Agent | Role |
|-------|------|
| **`spec-design-validator`** | Brutally validates specs, designs, and plans — hunts architectural flaws, unstated assumptions, missing requirements, and over-engineering. |
| **`team-lead`** | Orchestrator. Decomposes cross-domain work, resolves specialist conflicts, and authors technical design documents. |
| **`code-reviewer`** | Quality gate for correctness, security, maintainability, and comment quality. Used by the loop's review stages. |

### How the pieces fit together

```
agentic-loop  ──dispatches──►  code-reviewer          (spec/plan/code review gates)
      │
      └──invokes (Skill)──►  validating-specs  ──dispatches──►  spec-design-validator
```

`agentic-loop` depends on `validating-specs` for its spec/plan validation gate,
and on `code-reviewer` for its structured review passes. Installing this plugin
provides all three together.

## Installation

```bash
/plugin marketplace add simon-tanna/agent-loop-plugin
/plugin install spec-to-pr@spec-to-pr-marketplace
```

Restart Claude Code after installing.

### Local development / testing

From a clone of this repo:

```bash
/plugin marketplace add /path/to/agent-loop-plugin
/plugin install spec-to-pr@spec-to-pr-marketplace
```

## Hooks (optional, per-repo opt-in)

This plugin does **not** auto-register hooks globally. The `agentic-loop` skill
ships a set of hooks under `skills/agentic-loop/setup/` that you opt into **per
repository** by following that skill's `setup/SETUP.md`. This keeps the loop's
guardrail hooks scoped to repos where you actually run the loop, rather than
firing in every project. The set includes the loop's state-machine gate hooks
plus general defensive-security guardrails (block destructive git, block
env/secret reads, block secret exfiltration, block TypeScript violations).

## Requirements / platform support

- **Claude Code** (plugin support).
- Hooks and helper scripts are POSIX shell (`bash`) and use `jq`. They run
  natively on **macOS** and **Linux**. On **Windows**, run them under **Git Bash**
  (`bash` + `jq` on `PATH`); they are not written for Windows `cmd.exe`.

## Versioning & releases

See [RELEASING.md](./RELEASING.md). Versions follow semver in `plugin.json`;
update with `/plugin update spec-to-pr`.

## License

[MIT](./LICENSE) © Simon Tanna
