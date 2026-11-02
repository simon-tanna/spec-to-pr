# Native validator setup

## Optional project-local native validator

Run setup explicitly from an installed skill; validation never runs it for you.
Set SKILL to this installed skill's absolute directory and PROJECT to an existing
project directory. Python 3.10+ is sufficient; no checkout, sibling skill, plugin
root, package installation, or global writes are needed.

```bash
SKILL="/absolute/path/to/installed/spec-design-validator"
PROJECT="/absolute/path/to/project"
python3 "$SKILL/scripts/setup-validator.py" --host claude --project-root "$PROJECT"
python3 "$SKILL/scripts/setup-validator.py" --host codex --project-root "$PROJECT"
python3 "$SKILL/scripts/setup-validator.py" --host both --project-root "$PROJECT"
```

Choose one command. Omit `--project-root` to use the current working directory;
`--host claude|codex|both` is required. Claude writes
`.claude/agents/spec-design-validator.md`; Codex writes
`.codex/agents/spec-design-validator.toml`. Both copy ledger schema and project
checks into `.spec-to-pr/validator/references/` and record ownership hashes in
`.spec-to-pr/validator/ownership.json`. Unselected hosts and unrelated files stay
untouched. Codex adds only name, description and developer instructions; host
models, permissions, sandbox and MCP configuration stay under your control.
The Claude definition retains the plugin validator's model and denies Write,
Edit, NotebookEdit and Agent; Bash is not denied, so this is not a read-only
sandbox. Inspect actual runtime permissions for every child.

Reruns accept identical files and upgrade only files matching recorded ownership
hashes. All destinations are checked before writes; a conflict with unmanaged
content or local edits exits nonzero and writes nothing. Preserve your edits
and inspect each reported path; explicitly reconcile, restore or remove the
conflicting managed file before retrying. Each file is replaced atomically,
references before agent definitions and ownership last, so an I/O failure leaves
only complete files; the error lists them, and rerunning setup finishes the
install.

The installed definition is a copy of the rubric at setup time and embeds this
checkout's absolute reference path. Rerun setup after upgrading the skill and
after moving the project; modified managed files still require explicit
conflict resolution. Each checkout or clone runs its own setup.

Reload the host or start a new session after setup or upgrade. Installation
alone does not prove native discovery or spawning. Controllers prefer a native
validator only when the current exposed spawn schema has a selector accepting
the registered role; file presence is insufficient. Without that capability,
they use a fresh generic child with the bundled rubric as fallback. Explicit
generic selections stay generic. A started native failure, including a
rejected native spawn, follows the normal retry/stop policy rather than silently
switching worker types. On Claude Code the plugin agent takes precedence over a
project-local definition when both are registered. Validation reports record
which worker ran for each lens.

The Claude plugin already registers its plugin agent; skills installation alone
registers neither plugin agents nor hooks. Project setup is optional and separate
from that plugin registration. Independent review still requires a fresh reviewer
context. Native packaging makes no claim of better finding quality.
