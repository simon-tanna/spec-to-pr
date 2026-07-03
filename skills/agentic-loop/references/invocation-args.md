# Invocation Arguments — full reference

How the loop turns run-time flags into the resolved tooling every stage honours. Parsing happens once,
at **Stage 1 Ingest** (the single `$ARGUMENTS` site in `SKILL.md`); this file is the detailed contract.

## Grammar

```
[--skill a,b] [--mcp x,y] [--subagent t1,t2]
```

Comma-separated values, no spaces. The raw string arrives via `$ARGUMENTS` (a literal token substituted
at the Stage-1 parse block). Because that token is present, Claude Code does **not** append its usual
`ARGUMENTS:` trailer — the two are mutually exclusive — so read flags from the parse block and nowhere
else. **Empty or unsubstituted ⇒ no flags** (the normal headless/CI case; never treat a leaked literal
`$ARGUMENTS` as data). A `--token` outside `{skill, mcp, subagent}` is **echoed as unrecognised and the
run proceeds** (catches typos like `--subagant`); a *value* that resolves to nothing is **surfaced**
(interactive `AskUserQuestion`, headless `notify.sh blocked`), never silently dropped.

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

Validate against the **registered agent roster available at runtime** (the in-context agent list) — which
includes both plugin-namespaced agents (`voltagent-core-dev:backend-developer`) **and bare built-ins**
(`general-purpose`, `Explore`, `Plan`, `claude`). Namespacing is one valid form, **not** a requirement:
`--subagent general-purpose` is valid and accepted.

1. **Name resolution.** A token resolving to no registered `subagent_type` **halts before dispatch**
   (an unresolvable name also fails loudly at the `Agent(...)` call — validating early turns a mid-run
   crash into a clean up-front error).
2. **Code-capability — fail closed.** A specialist implements code, so it must be able to Write/Edit/Bash.
   Cite the agent's in-context `(Tools: …)` list and **reject any specialist whose capabilities cannot be
   positively confirmed to include Write + Edit + Bash** (unknown ⇒ reject). A read-only agent dispatched
   as an implementer silently no-ops with no harness backstop. Known read-only / deceptively-named classes
   to reject: `Explore`, `Plan`, `voltagent-research:*`, and `feature-dev:code-*` (their names say "code"
   but they cannot write files).
3. **Roster shape.** `agents.specialists` entries are `{type, owns}` objects that drive component-scoping
   and dispatch-plan validation. Adapt bare `--subagent` tokens:
   - single type ⇒ `{type, owns:"all code"}`
   - multiple types ⇒ `{type, owns:"code (planner allocates)"}` for each; `impl-planner.md` Mode-A Step 1
     is authorised to (re)allocate `owns` across them when it sees that placeholder.

Surface failures the same way everywhere: interactive `AskUserQuestion`; headless `notify.sh blocked`
(a setup-class message handled like `BLOCKED_PERMISSION`) — **never** the `questions` interview-exit path
(that would collide with the notify-and-exit and Stage-3 no-ping rules).

## `--mcp` compatibility gate

A subagent can only call an `mcp__…` tool if its allow-list contains **both** `ToolSearch` and the
`mcp__…` tool. MCP-server *inheritance* (subagents inherit the parent CLI's MCP servers — see
`SKILL.md` §External Research) grants *connection access* but **cannot add tools** to a restricted
agent's allow-list. So:

- Only **wildcard-tool** specialists (`general-purpose`, `spec-to-pr:team-lead`, `claude`, any `All tools`
  agent) can satisfy `--mcp` on the **implementation** hop.
- Named code specialists (`voltagent-*`, `feature-dev:code-*`) have fixed tool lists **without**
  `ToolSearch`/`mcp__` — they cannot, and inheritance does not change that.
- **At parse time**, if `--mcp` co-occurs with a `--subagent` known to lack `ToolSearch`, warn (surface
  via the mechanism above) rather than emitting a REQUIRED-MCP line the specialist can never load.
- The `validating-specs` hop is `All tools`, so `--mcp` is always satisfiable there — the loop forwards
  `--mcp` to that pass regardless.

## REQUIRED TOOLING block (owned fork)

> Forked from `spec-to-pr:validating-specs` `prompts/validator-instance.md` (its REQUIRED TOOLING block).
> Sibling skill trees cannot safely cross-reference at runtime, so this is an intentional copy — **keep it
> in sync** whenever the ToolSearch-before-MCP rule changes there.

Prepend to each dispatched specialist / research prompt whose run has required tooling. Expand the
`{{#each}}` by hand — one bullet per skill/MCP; drop the block entirely if the run has none:

```
REQUIRED TOOLING — you MUST use each of these before delivering your work:
{{#each REQUIRED_SKILLS}}
- Skill tool: invoke `{{name}}` — {{reason}}. Do not reason about this from memory.
{{/each}}
{{#each REQUIRED_MCPS}}
- {{name}} MCP: FIRST load its schema with
  `ToolSearch` query "{{toolsearch_query}}"
  (you cannot call an mcp__ tool until its schema is loaded), THEN use it to {{reason}}.
  Query the narrowest topic that settles the specific claim in doubt — do not pull broad overviews.
{{/each}}
```

Note on inheritance vs. schema-load: inheriting the MCP *server* makes the tool *available*; `ToolSearch`
still loads the tool *schema* before the first `mcp__` call. The two are not the same — do not drop the
ToolSearch line because the server is inherited.

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
