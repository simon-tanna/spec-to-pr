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
    "reviewer": "code-reviewer",

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
  "risk_categories": []
}
```

## Auto-detect defaults (config absent)

| Concern        | Default behaviour                                                                       |
| -------------- | --------------------------------------------------------------------------------------- |
| `base_ref`     | `main`                                                                                   |
| quality gates  | `scripts/quality-gates.sh` detects the package manager from the lockfile and runs only the `package.json` scripts that exist among `test`/`lint`/`typecheck`/`build`; for non-JS repos it falls back to `cargo test` / `go test ./...` / `pytest`. See that script for the exact precedence and the no-gate-detected safety behaviour. |
| `agents.planner`   | `general-purpose`                                                                    |
| `agents.reviewer`  | `code-reviewer` if available, else `general-purpose` (degraded)                      |
| `agents.specialists` | `[{ "type": "general-purpose", "owns": "all code" }]`                              |
| `risk_categories`  | the generic set only                                                                |
