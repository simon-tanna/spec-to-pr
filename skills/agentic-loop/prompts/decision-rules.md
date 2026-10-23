# Decision rules

The controller prepends this file to the spec-planner, spec-reviewer, plan-reviewer, and task-implementer prompts, so every child classifies decisions against one copy. The spec planner and spec reviewer apply all three sections; the plan reviewer and task implementer apply `## Load-bearing decision`.

## Source signals

A source signal is prose in `source.md` showing the human wants an interview round before the spec locks.

Match a phrase only when the source author wrote it as prose. A phrase inside a markdown table cell, a fenced code block, a quoted citation, or material the source asks you to read about something else is not a signal.

Phrases (case-insensitive):

- "stop and ask"
- "if anything is unclear"
- "if unclear"
- "design decisions" (as a directive, not a section heading you are reading)
- "product decisions" (as a directive, not a section heading you are reading)
- "ask the human"
- "ambiguous" (as a self-flag, not an adjective the source applies to a third thing)
- "unresolved" (as a self-flag, not a generic adjective)
- "open question" / "open questions" (as a self-flag, not a section heading you are reading)
- "to be decided" / "tbd"
- "unsure" / "not sure" (as a self-flag from the source author)
- "either" / "could go either way" (applied to the source's own decision, not to a third thing)

Structural pattern: a line whose trimmed text starts with `Default:`. A `Default:` inside a markdown table row (`| something | Default: ... |`) is not a signal.

## Two-alternatives test

For each decision, ask: *is there a second defensible option a competent engineer on this team might pick?* If yes, the decision is product-level and goes to §9 Open Questions unless `source.md` authorises the chosen answer. If you cannot name a second option, the decision is process and stays in §8 Resolved Decisions with its rationale. The bar is "a second defensible option exists", not "the optimal answer is non-obvious".

**Authorisation** means `source.md` literally says "use X", "X is required", or "X — confirmed", or the human answered a prior §9 question with X. "Default: X", "standard practice is X", and "we usually do X" are not authorisation.

The test applies in every category:

- **Load-bearing**: every category in `## Load-bearing decision` below.
- **Architecture**: data shape, storage format, sync vs async, push vs pull, integration topology, error model, retry strategy, idempotency model, event vs polling.
- **Library**: any concrete library, version, or third-party API endpoint `source.md` does not name. Matching an existing codebase convention 1:1 (the same library analogous modules already use) is process; introducing a new dependency is product-level.
- **Threshold**: timeouts, retry counts, batch sizes, page sizes, fee bps, deadlines, cache TTLs, rate limits, fan-out limits. A number `source.md` does not state goes to §9.

Process decisions: codebase conventions matched 1:1 to existing files, formatter and linter settings, language idioms, the genuinely one-of-one choice.

Frame each decision the test moves to §9 as:

> Confirm: <decision>? Suggested default: <X> (alternative considered: <Y>, because <one-line reason a sane engineer might pick it>)

The named alternative is the evidence that the test ran.

## Load-bearing decision

A *load-bearing decision* is a decision in any category below. It is always product-level: the human resolves it unless `source.md` literally authorises the answer. A specialist's recommendation in one of these categories is input to the question, never the answer.

<!-- load-bearing-categories:start -->
- **Access control and authorization**: who may perform which action; roles, scopes, tenancy, privileged and emergency paths.
- **Data custody and ownership**: who holds the data or keys, where they live, which system is the record.
- **Data retention and privacy**: PII handling, deletion, residency.
- **Irreversible or destructive operations**: deletes, data migrations, bulk mutations, anything not safely undoable.
- **Billing and money movement**: charges, fees, refunds, quotas, metering, who pays and who receives funds.
- **Migration, rollout, and upgrade authority**: who may run migrations or upgrades, rollout and rollback control.
- **Third-party and external-service trust boundaries**: which component or external service may mutate which state, and how that call is authenticated.
- **Attack surface**: new or widened entry points, exposed endpoints or inputs, and changes to security posture.
- **Breaking public-contract changes**: API, schema, CLI, or event-payload changes that break existing consumers.
<!-- load-bearing-categories:end -->

Each item in the `risk_categories` array of the repo's `.agentic-loop.config.json`, when that file exists, is a load-bearing category too.
