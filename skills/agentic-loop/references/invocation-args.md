# Invocation Arguments — full reference

How the loop turns run-time flags into the resolved tooling every stage honours. Parsing happens once,
at **Stage 1 Ingest** (`spec-loop.md` step 1.2, which reads the single `$ARGUMENTS` site in `SKILL.md`); this file is the detailed contract.

## Grammar

```
[--skill a,b] [--mcp x,y] [--subagent t1,t2]
```

Comma-separated values, no spaces. Parse once at Stage 1 ingest. Claude may
supply a substituted argument block; otherwise use the actual invocation and
user request. An empty or unsubstituted placeholder is not a flag value and does
not override flags present in the request. Unknown flags are echoed as
unrecognised while the run proceeds. A named value that cannot be resolved is a
setup failure, surfaced through the available interactive question interface or
headless `notify.sh blocked`; never silently drop a required value.

## Resolution & precedence — args win, config augments

Build `run-requirements.json = { skills[], mcps[], specialists[] }`:

| Field         | Rule                                                                                          |
| ------------- | --------------------------------------------------------------------------------------------- |
| `skills`      | `dedup(--skill ∪ config.required.skills)` — a name in both collapses to one.                   |
| `mcps`        | `dedup(--mcp ∪ config.required.mcps)`.                                                          |
| `specialists` | `--subagent` (if present) **fully replaces** the roster; else `agents.specialists`; else `[{type:"general-purpose", owns:"all code"}]`. |

`run-requirements.json` is **write-once at ingest** and **immutable** thereafter: on resume it is
re-loaded, never re-parsed, and `$ARGUMENTS` is ignored (a local resume with different flags does not
mutate a committed run config).

## `--subagent` validation (before any Stage 2 dispatch)

Resolve through `references/dispatch.md`, preserving configured names in durable
requirements and mapping to the harness only at dispatch:

1. **Name resolution.** `general-purpose` maps to a generic fresh child. Bundled
   `code-reviewer`, `team-lead`, and `spec-design-validator` bare names and
   `spec-to-pr:` aliases map to their packaged roles. Claude may select native
   registered roles or generic children carrying these roles. Codex uses its
   exposed spawning interface. Every other explicitly selected name must resolve
   to a native agent available in this harness; never silently substitute one.
2. **Code capability — fail closed.** An implementer must be able to read, edit,
   and execute the required checks in the target checkout. Verify exposed child
   capabilities, not a particular spelling such as Write/Edit/Bash. Unknown or
   read-only capabilities cannot satisfy implementation. A review-only bundled
   role cannot be selected as an implementer merely because its underlying
   generic child has write tools.
3. **Roster shape.** `agents.specialists` entries are `{type, owns}` objects that drive component-scoping
   and dispatch-plan validation. Adapt bare `--subagent` tokens:
   - single type ⇒ `{type, owns:"all code"}`
   - multiple types ⇒ `{type, owns:"code (planner allocates)"}` for each; `impl-planner.md` Mode-A Step 1
     is authorised to (re)allocate `owns` across them when it sees that placeholder.

Surface setup failures through the available interactive question interface or
headless `notify.sh blocked`, never the product interview exit path.

## Required tooling compatibility

Required tools must be usable inside the fresh child before dependent work.
Parent MCP access does not prove child access: native restrictions, feature flags,
and harness configuration can change the child's available tools. Discover
schemas through the actual exposed interface when deferred (Claude may expose
ToolSearch), then require actual tool use relevant to the task. Missing required
MCP or skill access stops the dependent stage with setup guidance. Do not remove
a requirement from the prompt because a selected child cannot satisfy it.

Skills may be loaded via a native skill tool or by reading the resolved absolute
SKILL.md path and its resources. Supplying a name without accessible instructions
is insufficient. The controller may verify discovery early, but the child still
verifies access before its dependent work.

## REQUIRED TOOLING block

Prepend this to every specialist, researcher, or reviewer for which tooling is
required. Expand authoring placeholders into one concrete bullet per requirement;
no template engine is implied. Resolve resource paths from the installed skill.

```
REQUIRED TOOLING — verify access before dependent work; report failure and stop
if a required tool or skill is unavailable. Do not substitute recalled facts.
- Skill <name>: read/apply <absolute SKILL.md path or exposed skill invocation>.
  Reason: <task-specific reason>.
- MCP <name>: discover its callable schema using the current harness if deferred,
  then use it to <task-specific verification>. Cite the result. Parent access
  does not establish your access.
```

## Config equivalent (headless/CI)

A GitHub Action run has no typed flags, so `$ARGUMENTS` is empty and the set is sourced from config:

```jsonc
{
  "required": { "skills": ["your-db-skill"], "mcps": ["context7"] },
  "agents":   { "specialists": [{ "type": "general-purpose", "owns": "all code" }] }
}
```

Same resolution rules; config-sourced skills/MCPs are forwarded to `validating-specs` exactly like
flag-sourced ones.
