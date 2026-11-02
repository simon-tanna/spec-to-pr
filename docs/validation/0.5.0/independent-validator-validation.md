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
- Independent branch review found lens-scoping and report-boundary defects;
  both were corrected. A report-boundary regression failed before the fix.

## Incomplete

- INCOMPLETE: Codex 0.166.0 dispatch smoke exited 1 with no observed child.
- INCOMPLETE: Claude dispatch smoke exited 1 before observing a completed child.
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
