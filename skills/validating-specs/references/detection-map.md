# Detection Map: spec content → skill / MCP

Scan the spec for these signals and add the mapped skill/MCP to the **required tooling**
of the instance owning the listed lens. **User `--skill` / `--mcp` flags always apply on
top of this** — auto-detect only adds, never removes.

When you add a tool, always pair it with the _reason_ in the instance prompt (e.g. "use the
`cel` skill — it has cel-js bigint/list-membership details general knowledge gets wrong").

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

| Spec signals (keywords / topics)                                                                                                                                                                 | Skill               | Lens                         |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------- | ---------------------------- |
| CEL, cel-js, `celExpression`, policy expression, expression cache, fail-closed, bigint in CEL                                                                                                    | `cel`               | domain                       |
| policy engine, `LoadedPolicyRule`, `LoadedPolicySet`, multicall ruleset, `decode_hints`, evaluation pipeline, OR-within/AND-across, rule matching, siwe / personal_sign / EIP-712 message policy | `policy-evaluation` | domain                       |
| Fordefi, MPC wallet, vault, transaction approval, validator bot, signing flow                                                                                                                    | `fordefi`           | domain                       |
| Fordefi **webhook**, X-Signature, approve/abort endpoint, `evm_message`, P-256 signature verification                                                                                            | `fordefi-webhooks`  | domain / security            |
| D1, Drizzle, SQLite, migration, schema, table, integration test against DB                                                                                                                       | `miniflare-d1`      | domain / scope (testability) |
| Terraform, OpenTofu, infra module, `.tf`, state, provider                                                                                                                                        | `terraform`         | architecture                 |
| `turbo.json`, monorepo, package boundary, catalog dep, build caching, `--affected`, workspace                                                                                                    | `turborepo`         | architecture                 |
| Clerk, authentication, sign-in/up, organizations, billing, `createServerFn` auth, `beforeLoad` guard                                                                                             | `clerk`             | domain / security            |

## MCP servers

| Spec signals                                                                                                                                                             | MCP server           | Lens                      | Note                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------- | ------------------------- | ------------------------------------------------------------------------------------- |
| **Version-specific / migration** claim, or an **unfamiliar / less-common** library / SDK / API (skip for ubiquitous, stable libs unless a version/API claim is in doubt) | `context7`           | the lens making the claim | `resolve-library-id` → `query-docs`; query the narrowest topic, not a broad overview. |
| Cloudflare Workers, wrangler, KV, R2, Durable Objects, Workers AI, Vectorize, Hyperdrive                                                                                 | `cloudflare-docs`    | architecture              | `search_cloudflare_documentation`                                                     |
| Turnkey, sub-org, WebAuthn passkey via Turnkey, session keys                                                                                                             | `Mintlify` (turnkey) | domain                    | `search_turnkey` / `query_docs_filesystem_turnkey`                                    |
| References a ticket/issue (ROCK-NNNN, Linear) for requirements context                                                                                                   | `Linear`             | scope                     | Pull the issue to check spec vs. stated requirements                                  |
| References a GitHub issue/PR (#NNN) for context                                                                                                                          | `github`             | scope                     |                                                                                       |
| 1inch, swap, limit order, Fusion, cross-chain swap                                                                                                                       | `1inch`              | domain                    |                                                                                       |

## Lens trigger keywords (for fan-out decisions)

Add a **`security`** instance when the spec mentions any of:
auth, JWS, JWE, KMS, signing, private key, secret, credential, cosigner, webhook signature
verification, reentrancy, access control, on-chain attack surface, `process.env`, token/session.

The **`domain`** lens is warranted whenever the spec encodes project-specific business logic
(policy/CEL semantics, Fordefi flows, vault accounting, on-chain contract behavior) rather than
generic CRUD/UI.

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
