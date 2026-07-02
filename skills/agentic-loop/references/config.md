# Repo Configuration — `.agentic-loop.config.json`

The loop is repo-agnostic. Everything that varies between repositories is read from an
**optional** `.agentic-loop.config.json` at the repo root. When the file is absent, the loop
auto-detects sensible defaults, so a fresh repo runs zero-config. When present, its values
override the defaults. Read it once at loop start (Stage 1 ingest).

## Shape

```jsonc
{
  // Default branch the loop targets for branch-off, PR base, and full-branch diffs.
  // Resolution order: this field → issue "Base branch:" field → "base:<ref>" label → "main".
  "base_ref": "main",

  // Quality-gate commands. Any key omitted → auto-detected from the toolchain.
  // A key set to "" → that gate is explicitly skipped (acknowledged, not silently dropped).
  // The whole object set to {} → ALL gates opted out (the loop ships with no verification —
  // use only for repos that genuinely have no runnable checks).
  "quality_gates": {
    "test":      "pnpm test",
    "lint":      "pnpm lint",
    "typecheck": "pnpm typecheck",
    "build":     ""
  },

  // Agent roster. All optional; defaults shown.
  "agents": {
    // The planner/synthesizer. Returns tagged artifacts the controller writes — it never
    // makes Agent calls itself. Default: "general-purpose" (a real, model-tierable dispatch).
    // A bespoke orchestrator agent (e.g. "team-lead") is one valid value.
    "planner": "general-purpose",

    // The review agent for spec/plan/compliance/quality/final passes and the adversarial
    // attack-surface pass. Default: "code-reviewer"; falls back to "general-purpose" with a
    // documented loss of review tuning (see SKILL.md "Model Tiering" / plan-loop adversarial pass).
    // Installed via the spec-to-pr plugin, the bundled reviewer is "spec-to-pr:code-reviewer";
    // set that as the value (or dispatch by that plugin-qualified name) so the tuned agent is used
    // rather than the general-purpose fallback.
    "reviewer": "spec-to-pr:code-reviewer",

    // Domain specialists the planner may route tasks to. The controller validates every
    // dispatch_plan agent_type against this list. Default: a single general-purpose owner.
    "specialists": [
      { "type": "general-purpose", "owns": "all code" }
    ]
  },

  // Extra repo-specific load-bearing decision categories appended to the generic set
  // (auth/access, data ownership, irreversible ops, money/fees, retention/PII, trust
  // boundaries, external-service trust, breaking public-contract changes). Drives the
  // decision-fork interview and the adversarial attack-surface review pass.
  "risk_categories": [],

  // I/O adapter for all human-facing messages (banners, open questions, progress,
  // escalations) and PR creation — see SKILL.md §Operating Modes, Axis B. Absent ⇒
  // "github" when the gh CLI is authenticated (or $GITHUB_ACTIONS=true), else "file"
  // (a gh-free sandbox writes to .agentic-loop/<id>/notifications.md and pauses).
  // Overridable at runtime via $AGENTIC_IO_ADAPTER.
  "io": {
    "adapter": "github",     // "github" | "file" | "webhook" | "command"
    "webhook_url": "",        // adapter=="webhook"; or $AGENTIC_NOTIFY_WEBHOOK
    "notify_command": ""      // adapter=="command"; executable receiving (kind, id) argv + body on stdin
  }
}
```

## Auto-detect defaults (config absent)

| Concern        | Default behaviour                                                                       |
| -------------- | --------------------------------------------------------------------------------------- |
| `base_ref`     | `main`                                                                                   |
| quality gates  | `scripts/quality-gates.sh` detects the package manager from the lockfile and runs only the `package.json` scripts that exist among `test`/`lint`/`typecheck`/`build`; for non-JS repos it falls back to `cargo test` / `go test ./...` / `pytest`. See that script for the exact precedence and the no-gate-detected safety behaviour. |
| `agents.planner`   | `general-purpose`                                                                    |
| `agents.reviewer`  | `spec-to-pr:code-reviewer` (the bundled agent) if available, else `general-purpose` (degraded) |
| `agents.specialists` | `[{ "type": "general-purpose", "owns": "all code" }]`                              |
| `risk_categories`  | the generic set only                                                                |
| `io.adapter`       | `github` if the gh CLI is authenticated or `$GITHUB_ACTIONS=true`, else `file`      |
