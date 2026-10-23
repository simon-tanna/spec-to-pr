# Detection Map: spec content → tooling

The validation workflow's step 4 (Resolve tooling) matches spec content against these rows. A match the user didn't name is **optional** tooling for the listed lens's instance; pass its Reason. A row applies only when its skill or MCP exists in this environment — skip a row whose skill or server is absent from the skill listing or tool discovery.

## Project skills

| Spec signals | Skill | Lens | Reason |
| --- | --- | --- | --- |

<!-- Customize: add one row per skill your repo installs. Examples:
| ORM / query builder, migration, schema, table, integration test against the DB | `your-db-skill` | domain / scope | migration-ordering and transaction-boundary details general knowledge gets wrong |
| Infrastructure-as-code, infra module, provider, state file | `your-iac-skill` | architecture | provider and state-file semantics specific to your IaC tool |
| Monorepo, package boundary, workspace, build caching, affected-graph | `your-monorepo-skill` | architecture | your workspace layout, package boundaries, and build-graph rules |
| Authentication, sign-in/up, sessions, organizations, route guards | `your-auth-skill` | domain / security | your auth provider's session, organization, and guard model |
-->

## MCP servers

| Spec signals | MCP server | Lens | Reason |
| --- | --- | --- | --- |
| **Version-specific / migration** claim, or an **unfamiliar / less-common** library / SDK / API (skip for ubiquitous, stable libs unless a version/API claim is in doubt) | `context7` | the lens making the claim | verify the claim: `resolve-library-id` → `query-docs`, narrowest topic that settles it; user/project rules requiring Context7 more broadly win |
| References a GitHub issue/PR (#NNN) for context | `github` | scope | pull the issue to check the spec against its stated requirements |

<!-- Customize: add your tracker and platform-docs MCP servers. Examples:
| References a project tracker ticket (e.g. `TICKET-NNNN`) for requirements context | your tracker MCP (Linear, Jira, …) | scope | pull the ticket to check the spec against its stated requirements |
| Mentions a specific cloud/platform SDK or an internal service with its own docs MCP | that service's docs MCP | architecture | verify SDK and service claims against current docs |
-->
