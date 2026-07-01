# Detection Map: spec content → skill / MCP

Scan the spec for these signals and add the mapped skill/MCP to the **required tooling**
of the instance owning the listed lens. **User `--skill` / `--mcp` flags always apply on
top of this** — auto-detect only adds, never removes.

When you add a tool, always pair it with the _reason_ in the instance prompt (e.g. "use the
`your-db-skill` skill — it has migration-ordering and transaction-boundary details general
knowledge gets wrong").

## Doc-type signals (for the step 2.5 classification)

Classify the artifact by **filename suffix first, content second — never by directory**
(`docs/plans/` holds both `*-plan.md` and `*-design.md` for the same change).

| Signal                                                                                 | Doc-type                           |
| -------------------------------------------------------------------------------------- | ---------------------------------- |
| Filename `*-plan.md`, or headings `## Task N` / `## Phase N` / sequenced steps         | execution plan                     |
| Filename `*-design.md`, or `## Decisions` / `## Module Structure` / `## Test Strategy` | design doc                         |
| Filename `*-spec*` / `*-prd*`, or requirements + acceptance-criteria blocks            | spec / PRD                         |
| A few lines / one obvious ask                                                          | task card                          |
| None of the above resolve                                                              | unclassified → size-based fallback |

Doc-type sets the **default lens split** (SKILL.md step 3), not which skills/MCPs attach.

## Project skills

> **Customize this table for your project.** The rows below are illustrative
> examples of the mechanism: map spec keywords to a skill your repo installs and
> the review lens that skill sharpens. Replace them with your own stack's skills
> (your auth provider, your ORM/DB layer, your IaC tool, your domain libraries).

| Spec signals (keywords / topics)                                                        | Skill (example)     | Lens                         |
| --------------------------------------------------------------------------------------- | ------------------- | ---------------------------- |
| ORM / query builder, migration, schema, table, integration test against the DB          | `your-db-skill`     | domain / scope (testability) |
| Infrastructure-as-code, infra module, provider, state file                              | `your-iac-skill`    | architecture                 |
| Monorepo, package boundary, workspace, build caching, affected-graph                     | `your-monorepo-skill` | architecture               |
| Authentication, sign-in/up, sessions, organizations, route guards                        | `your-auth-skill`   | domain / security            |

## MCP servers

| Spec signals                                                                                                                                                             | MCP server           | Lens                      | Note                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------- | ------------------------- | ------------------------------------------------------------------------------------- |
| **Version-specific / migration** claim, or an **unfamiliar / less-common** library / SDK / API (skip for ubiquitous, stable libs unless a version/API claim is in doubt) | `context7`           | the lens making the claim | `resolve-library-id` → `query-docs`; query the narrowest topic, not a broad overview. |
| References a GitHub issue/PR (#NNN) for context                                                                                                                          | `github`             | scope                     | Pull the issue to check spec vs. stated requirements                                  |
| References a project tracker ticket (e.g. `TICKET-NNNN`) for requirements context                                                                                        | your tracker MCP     | scope                     | Add your issue tracker's MCP server here (Linear, Jira, …)                             |
| Mentions a specific cloud/platform SDK or an internal service with its own docs MCP                                                                                      | that service's docs MCP | architecture           | Add your platform/service documentation MCP servers here                              |

## Lens trigger keywords (for fan-out decisions)

Add a **`security`** instance when the spec mentions any of:
auth, JWS, JWE, KMS, signing, private key, secret, credential, webhook signature
verification, access control, injection/attack surface, `process.env`, token/session.

The **`domain`** lens is warranted whenever the spec encodes project-specific business logic
(your project's core rules, workflows, and invariants) rather than generic CRUD/UI.

Add an **`execution`** instance when the artifact is an execution/implementation plan or mentions
any of: phases, milestones, sequencing, dependency ordering, critical path, parallel workstream,
estimate/timeline, rollback, migration, rollout, cutover, feature flag, review gate, test gate.
(Sequencing/rollback/gates belong to `execution`, **not** `scope` — keep them disjoint.)

## CRITICAL: making a subagent actually use an MCP

A subagent cannot call `mcp__…` tools until it loads their schemas via `ToolSearch`. When an
instance prompt requires an MCP, it MUST instruct the subagent to first run, e.g.:

```
ToolSearch with query "select:mcp__plugin_context7_context7__resolve-library-id,mcp__plugin_context7_context7__query-docs"
```

(or a keyword query like `ToolSearch "context7 docs"`), THEN call the tool. Naming the tool
without this step results in an InputValidationError and the subagent silently skips the check.
