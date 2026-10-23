# spec-to-pr

An independently installable skills suite for interactive Codex and Claude Code,
with an optional Claude Code plugin distribution. It bundles an autonomous
**spec → PR** loop with the supporting skills and agents it relies on: spec
validation, code review, and documentation.

## What's inside

### Skills

| Skill | What it does |
|-------|--------------|
| **`agentic-loop`** | The flagship pipeline. Takes a spec, task card, or GitHub issue and drives it end-to-end: planning → spec/plan validation gates → TDD execution loop → review loops → PR. Invoke it with "run the agentic loop", "implement this issue", or "take this from spec to PR". |
| **`validating-specs`** | Pressure-tests a spec, design doc, or implementation plan before engineering starts, dispatching a fresh child with the bundled validator role. Returns a `GO` / `REVISE` / `NO-GO` verdict. |
| **`writing-documentation`** | Produces structured technical documentation using the [Diátaxis](https://diataxis.fr/) framework. Places each document in one quadrant (tutorial, how-to, reference, explanation) via the compass, grounds every claim against source, and also audits an existing doc set for quadrant purity and accuracy. |

### Roles and optional native agents

Each skill bundles the role instructions it needs. Claude plugin installation also
registers native agents; skills-only installation supplies the same instructions
to generic fresh children. Required validation and review stop if the harness
cannot create an independent child.


| Agent | Role |
|-------|------|
| **`spec-design-validator`** | Brutally validates specs, designs, and plans — hunts architectural flaws, unstated assumptions, missing requirements, and over-engineering. |
| **`team-lead`** | Orchestrator. Decomposes cross-domain work, resolves specialist conflicts, and authors technical design documents. |
| **`code-reviewer`** | Quality gate for correctness, security, maintainability, and comment quality. Used by the loop's review stages. |

### How the pieces fit together

`agentic-loop` contains its validation workflow and reviewer roles, so installing
it alone works without a sibling `validating-specs` installation. The standalone
validator remains useful for review-only work. Generated copies keep shared
instructions consistent across the suite and Claude plugin agents.

## Quick start: from spec to PR

1. **Install** the skills or Claude plugin (see [Installation](#installation)) and start a fresh harness session.
2. **Point `agentic-loop` at a spec** — a GitHub issue, task card, or written feature
   description:

   ```text
   /spec-to-pr:agentic-loop implement issue #42
   ```

   or hand it off in prose ("take this from spec to PR"). The slash command above
   is the Claude plugin form; standalone installations use the skill name
   `agentic-loop`. The optional Claude plugin nudge helps detect spec-shaped prompts.
3. **Answer the design questions.** Interactively, the loop asks them via
   the harness question interface at the spec and plan gates; it will not start coding until the spec
   and plan pass validation.
4. **Let it run.** The loop plans, validates the spec and plan (dispatching
   the bundled validation workflow), executes the tasks test-first,
   runs its review passes, and opens one PR.

Registering the gate hooks (see [Hooks](#hooks)) is optional but makes those gates
deterministic rather than model-enforced.

With the Claude plugin, invoke the other two skills the same way:

```text
/spec-to-pr:validating-specs docs/checkout-spec.md
/spec-to-pr:writing-documentation add a how-to for the payments webhook
```

## Steering a run

Pin the skills, MCP servers, and implementation subagents a single run uses by
appending flags to the invocation — no config edit needed:

| Flag | Effect |
|------|--------|
| `--skill a,b` | Require these project skills; the run and its subagents consult them. |
| `--mcp x,y` | Require these MCP servers for research and verification. |
| `--subagent t1,t2` | Set the specialist roster that implements the code (`agentic-loop` only; bundled roles and `general-purpose` are portable; other names must be available in the harness). |

```text
/spec-to-pr:agentic-loop implement issue #42 --skill payments-db --mcp context7
/spec-to-pr:validating-specs docs/checkout-spec.md --skill payments-db --mcp context7
```

A headless or CI run has no typed flags, so set the same tooling in
`.agentic-loop.config.json` — a `required: { skills, mcps }` block, plus
`agents.specialists` for the roster.

Required MCP access must be verified in each child; parent tool availability
does not prove child access. Claude named-agent tool restrictions still apply. Full grammar and rules live in
[`skills/agentic-loop/references/invocation-args.md`](skills/agentic-loop/references/invocation-args.md).

## Installation

### Skills suite: Codex and Claude Code

Run from the project where you want the skills installed:

```bash
pnpm dlx skills add simon-tanna/spec-to-pr --skill '*' -a codex -a claude-code -y
```

For one skill, replace `--skill '*'` with `--skill agentic-loop`,
`--skill validating-specs`, or `--skill writing-documentation`. Add `-g` for a
user-wide installation, or `--copy` to copy files into agent directories instead
of the default links. No npm release of this repository is needed: the installer
reads the GitHub repository and includes each skill's supporting resources.
The repository command installs published GitHub content; for unreleased changes,
replace `simon-tanna/spec-to-pr` with the absolute path to a local checkout.

Skills installation does not register Claude plugin hooks or native agents.
The bundled dispatch instructions supply roles to fresh generic children in both
harnesses. Codex omits model overrides and uses the harness's effective defaults.

### Optional Claude plugin

```text
/plugin marketplace add simon-tanna/spec-to-pr
/plugin install spec-to-pr@spec-to-pr-marketplace
```

Restart Claude Code after installing. This distribution additionally registers
Claude native agents and the prompt nudge. Avoid installing both distributions
for the same harness unless you intentionally want duplicate skill entrypoints.

### Local development / testing

From a clone of this repo:

```bash
/plugin marketplace add /path/to/spec-to-pr
/plugin install spec-to-pr@spec-to-pr-marketplace
```

## Hooks

These hooks apply to Claude Code. Skills-only Codex runs invoke the shared gate
checks through the controller; they do not install lifecycle interception.

The plugin ships hooks in **two layers**.

**Plugin-level (always active).** Installing the plugin registers one
`UserPromptSubmit` hook, `inject-agentic-loop-nudge.sh`. It detects spec-shaped
prompts and nudges Claude to invoke `agentic-loop` before falling into plain plan
mode. It only nudges — it never blocks — and no-ops in CI, when a loop is already
running, and after firing once per session. Opt out with `AGENTIC_LOOP_NO_NUDGE=1`.

**Per-repo (opt-in).** The `agentic-loop` skill ships gate, context, and security
hooks under `skills/agentic-loop/setup/`. The plugin does **not** auto-register
these — you enable them per repository, so they fire only where you run the loop.
Registered, the gate hooks make the stage gates *deterministic* (the harness blocks
the offending tool call); unregistered, the loop's controller still self-enforces
them.

### Hook reference

| Hook | Layer | Event (matcher) | What it does | In snippet |
|------|-------|-----------------|--------------|:-:|
| `inject-agentic-loop-nudge.sh` | plugin | `UserPromptSubmit` | Nudges Claude to invoke `agentic-loop` on spec-shaped prompts | auto |
| `agentic-loop-check-state-transition.sh` | gate | `PreToolUse` (`Write\|Bash`) | Blocks a `.state` transition that skips the spec/plan preconditions | ✅ |
| `agentic-loop-check-tasks-json.sh` | gate | `PreToolUse` (`Write\|Edit`) | Blocks marking a task `done` without both review SHAs | ✅ |
| `agentic-loop-check-tdd-trace.sh` | gate | `PreToolUse` (`Write\|Edit`) | Blocks a `done` task whose commit lacks a test file and a `TDD:` line | ✅ |
| `agentic-loop-check-pr-ready.sh` | gate | `PreToolUse` (`Bash`) | Blocks `gh pr create` while any task or review is incomplete | ✅ |
| `postooluse-context-check.sh` | context | `PostToolUse` (`*`) | Drops an eject-flag when token use crosses the model threshold (headless) | ✅ |
| `precompact-flush.sh` | context | `PreCompact` | Flushes loop state to git before any compaction | ✅ |
| `block-destructive-git.sh` | opt-in | `PreToolUse` (you assign) | Blocks force-push, history rewrite, and branch/ref deletion | — |
| `block-env-reads.sh` | opt-in | `PreToolUse` (you assign) | Blocks reads of `.env`, secrets, and credential files | — |
| `block-secret-exfil.sh` | opt-in | `PreToolUse` (you assign) | Blocks env-dumps, token echoes, and network exfiltration | — |
| `block-ts-violations.sh` | opt-in | `PreToolUse` (you assign) | Blocks TypeScript edits that break the strict baseline (TS repos) | — |
| `force-agentic-loop.sh` | opt-in | `PreToolUse` (you assign) | CI-only: forces the first tool call to be the skill on a pinned branch | — |

The **snippet** is `skills/agentic-loop/setup/settings.snippet.json`; it registers the
six gate and context hooks. The five opt-in hooks are absent from it by design — copy
in each one you want and assign its matcher yourself.

### Enable the gate hooks in a repo

Ask Claude Code to run the setup for you — it resolves the plugin path
(`${CLAUDE_PLUGIN_ROOT}`, which a plain shell does not export) — following
[`setup/SETUP.md`](skills/agentic-loop/setup/SETUP.md) §3: copy the gate and context
hook scripts and their shared check dependencies into the repo's `.claude/hooks/`, merge the snippet into
`.claude/settings.json`, then run `check-substrate.sh` to confirm the gate hooks are
registered. SETUP.md holds the exact commands and the full CI substrate (env contract,
workflow, repo variables).

## Requirements / platform support

- **Codex or Claude Code** with fresh-child spawning for required validation/review.
- **Git**, a reachable `origin`, and a locally available base branch for loop
  initialization. Fresh runs require a clean tracked worktree and index;
  untracked source documents are allowed. See [interactive initialization](skills/agentic-loop/references/interactive-init.md).
- Hooks and helper scripts use `bash` and use `jq`. They run
  natively on **macOS** and **Linux**. On **Windows**, run them under **Git Bash**
  (`bash` + `jq` on `PATH`); they are not written for Windows `cmd.exe`.

## Verification status

The release adds automated packaging, initialization, and shared-gate tests.
Run `bash scripts/test.sh` for offline checks; see the
[validation record](docs/validation/0.3.0/portability-validation.md)
for test-first changes and remaining live acceptance work.
The [installation eval](docs/validation/0.3.0/installation-evidence.md)
passed eight isolated Skills CLI installs, including each skill alone and both
link/copy modes. These verify installation/resource closure and deterministic checks; they do not
establish complete live interactive execution on either harness. Record actual
versions and transcripts for fresh-child delegation, question/answer pause and
resume, negative gates, and a full fixture run before claiming end-to-end
compatibility. Missing live evidence remains an explicit acceptance gap.

The existing headless CI workflow remains Claude-only. Native Codex agent
configuration, Codex lifecycle hooks, and Codex headless CI are deferred.

## Versioning & releases

See [RELEASING.md](./RELEASING.md). Versions follow semver in `plugin.json`;
update with `/plugin update spec-to-pr`.

## License

[MIT](./LICENSE) © Simon Tanna
