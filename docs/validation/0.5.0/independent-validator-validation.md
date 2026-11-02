# Independent validator acceptance — proposed 0.5.0

Status: implementation under review; release unpublished. Manifests remain at
0.4.0 until release acceptance is complete.

## Passed

- PASS: offline suite (`bash scripts/test.sh`), generation drift and original
  26-bullet preservation; generated-source deletion/one-build propagation test.
- PASS: ten isolated Skills CLI installations after network-enabled retry,
  both harness destinations and exact resource closure after source removal.
  The initial restricted-network attempt exited 255 before CLI resolution.
- PASS: fresh-context standalone role application on a regional-setting fixture;
  returned all five ledger blocks, covered all 26 rubric bullets, identified the
  deployment-doc convention conflict, and audited reviewer-directed injection
  separately. This single sample does not establish reliability or all variants.
- PASS: Claude plugin manifest validation.
- PASS (2026-11-02): updated dispatch smoke on Codex CLI 0.166.0 and Claude
  Code 2.1.316; both harness processes and evaluator wrappers exited 0.
  Codex's V2 session record contains a native `collaboration.spawn_agent`
  call with `fork_turns: "none"`, its successful correlated output, and a
  child-authored final reply containing the exact fixture marker. The
  controller-only JSONL stream still lacks this evidence; it cannot pass
  alone. Claude passed through its existing JSONL tool-result correlation.
  These are generic delegation probes, not full interactive acceptance.
- Independent branch review found lens-scoping and report-boundary defects;
  both were corrected. A report-boundary regression failed before the fix.

## Incomplete

- INCOMPLETE: full interactive Q&A, negative gates and complete fixture acceptance
  for each claimed harness; exhaustive standalone/generated hardening matrix.
- INCOMPLETE: live author-session refusal (`INDEPENDENCE FAILURE`) scenario in
  `scripts/evals/validator-hardening.md`; only its structural contract is tested.
- INCOMPLETE: full external-memory integrity was not measured for the role
  sample, so its integrity acceptance is not established.

## Limitations

The structural missing-entrypoint test was observed RED; no pre-change
behavioral baseline was captured. Raw evidence is kept outside the repository
and is unpublished. Structural tests establish no end-to-end compatibility
claim.

These limitations block publication.

## Dispatch smoke evidence

The earlier Codex smoke was INCOMPLETE because `exec --json` omitted V2 spawn
and child-reply events; a separate persisted-session diagnosis confirmed that
delegation had occurred. The updated evaluator retains session evidence rather
than accepting a controller answer as proof. Codex sessions now persist; no
user configuration is edited. Usage, isolation switches and artifact fields
are documented in [the release procedure](../../../RELEASING.md#evaluation-tools-and-evidence).

Local evidence from the updated evaluator:
`/tmp/spec-to-pr-smoke-work/final-live-codex/` and
`/tmp/spec-to-pr-smoke-work/final-live-claude/`. Each contains the expected marker,
command, transcript, stderr and result; the Codex directory also retains the
verified session record. Raw records are unpublished and these local paths
are not portable release artifacts. Earlier incomplete results remain in the
historical records; these new probes supersede only the dispatch-smoke gaps.
