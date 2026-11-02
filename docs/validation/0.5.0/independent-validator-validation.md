# Independent validator acceptance — 0.5.0

Status: v0.5.0 authorized for publication with the known acceptance gaps below.
The maintainer explicitly accepted these gaps for this release on 2026-11-02;
they remain INCOMPLETE and do not establish end-to-end compatibility.

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

## Release preparation recheck (2026-11-02)

- PASS: offline regression suite, distribution drift check, Claude manifest
  validation, and ten isolated Skills CLI installations. The manifest validator
  reported a missing-icon warning.
- PASS: generic delegation smoke in both Codex and Claude with native child
  evidence; these checks do not establish interactive workflow acceptance.
- PASS: one Codex author-session refusal sample returned only
  `INDEPENDENCE FAILURE: This context authored the spec under review.` The
  local transcript and response are in `/tmp/spec-to-pr-author-refusal/`.

## Further Codex samples (2026-11-02)

Candidate resources at `5412978` were exercised with Codex CLI 0.166.0 in
separate fresh sessions and read-only shell sandboxes. The model was not
recorded by the captured JSONL, and sandboxing does not establish external
agent-memory integrity. Raw prompts, resource hashes, traces, outputs, and
before/after file and Git manifests are under
`/tmp/spec-to-pr-acceptance-20261102/`.

- PASS (worker A/B samples): standalone and generated roles both retained the
  ledger, covered all rubric IDs, identified the documentation convention and
  recorded both redirections. Files, Git status, index and history were unchanged.
  A separate `v0.4.0` generated-role baseline also ignored the redirections
  and identified the convention; it used its original four-block contract.
- PASS (generated worker D, full tooling): an exact web search and Context7
  resolution were observed, and the invented atomic API was reported as an
  unverified load-bearing `missing` finding with a verification fix.
- PASS (generated worker F): an empty target produced only the clarification
  line. Controller pause and resumption were not tested.
- INCOMPLETE (generated worker E): the missing-tool and missing-document runs
  returned capability failure lines; the JSONL lacks a tool-metadata discovery
  event for the missing server, so the former does not establish the required
  discovery probe. The controller retry/stop path remains untested.
- The D, E and F fixture files, Git status, index and history were unchanged.
  These are worker samples, not the complete distribution/harness matrix.

## Incomplete

- INCOMPLETE: full interactive Q&A, negative gates and complete fixture acceptance
  for each claimed harness; exhaustive standalone/generated hardening matrix.
- INCOMPLETE: author-session refusal has only the single Codex sample above;
  the broader standalone and generated hardening matrix remains unverified.
- INCOMPLETE: full external-memory integrity was not measured for the role
  sample, so its integrity acceptance is not established.

## Limitations

The structural missing-entrypoint test was observed RED; no pre-change
behavioral baseline was captured. Raw evidence is kept outside the repository
and is unpublished. Structural tests establish no end-to-end compatibility
claim.

The maintainer authorized publication of v0.5.0 with these limitations captured
as known gaps. This release-specific exception does not mark incomplete checks
as passing or change the standard release checklist.

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
