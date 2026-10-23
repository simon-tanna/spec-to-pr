# Generic dispatch smoke evidence

Observed 2026-10-23. This is a preliminary non-interactive capability probe,
not acceptance of the interactive skills suite.

The runner `run_portable_dispatch_smoke.py` writes a random marker into a disposable
fixture, instructs the controller to spawn a fresh generic reader, and requires
both a real spawn event and the marker in its child's result. A controller-only
answer cannot pass. Existing authentication is used; HOME and user configuration
are not changed. Child permissions are not bypassed. Each process group has a
bounded timeout. Traces and command lines are recorded in the supplied output
folder; inspect actual context arguments before claiming fresh-context semantics.

Reproduce:

```bash
python3 skills/agentic-loop-workspace/run_portable_dispatch_smoke.py --harness codex --output /tmp/spec-to-pr-live-codex --timeout 45
python3 skills/agentic-loop-workspace/run_portable_dispatch_smoke.py --harness claude --output /tmp/spec-to-pr-live-claude --timeout 45
```

| Harness | Result | Observed blocker |
| --- | --- | --- |
| Codex CLI 0.163.0 | INCOMPLETE; exit 1; no child events | `failed to initialize in-process app-server client: Operation not permitted (os error 1)` |
| Claude Code 2.1.309 | INCOMPLETE; exit 1; no child events | `authentication_failed`; `Not logged in · Please run /login` |

Claude's initialization event exposed `Task`, `Read`, `Glob`, and `Grep` despite
CLI tool arguments using the accepted `Agent` alias. The evaluator accepts actual
`Task` or `Agent` events. Neither invocation timed out or reached a model-backed
child dispatch. No authentication or sandbox workaround was attempted.

Raw local evidence: `/tmp/spec-to-pr-live-codex/{command.json,transcript.jsonl,stderr.log,result.json}`
and the same filenames under `/tmp/spec-to-pr-live-claude/`. These temporary paths
are evidence from this session, not portable release artifacts.

Five local parser assertions verified controller-only output rejection, successful
Codex spawn/result correlation, failed Codex child rejection, successful Claude
spawn/result correlation, and failed Claude tool-result rejection. These synthetic
checks validate the evaluator only; they do not replace live capability evidence.

A subsequent Codex invocation approved outside the outer execution sandbox
completed with exit 0. It produced an agent message containing the fixture marker,
but the captured collaboration events contained only `wait` with empty
`receiver_thread_ids` and empty `agents_states`. No actual spawn or correlated
child result was captured. Therefore its result remains **INCOMPLETE**, not PASS.
The outer initialization restriction was resolved; live delegation evidence was
still insufficient. That trace is in `/tmp/spec-to-pr-live-codex-unsandboxed/`.
The evaluator now accepts the observed `agents_states` field as well as the older
`agents` spelling, while requiring a matching spawned child ID and completed
result. Committed parser tests cover the observed incomplete trace.
