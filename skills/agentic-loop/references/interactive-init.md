# Interactive run initialization

Before ingesting into the pipeline, resolve the installed skill directory and run
`scripts/init-run.sh` from the target repository. This helper requires Git, Bash,
`jq`, and either `sha256sum` or `shasum`. It prints one JSON context object to
stdout; diagnostics go to stderr. A nonzero exit stops initialization.

```bash
bash "$SKILL_DIR/scripts/init-run.sh" --source-file /absolute/path/spec.md
bash "$SKILL_DIR/scripts/init-run.sh" --source-file /absolute/path/issue.md --issue 42 --title 'Add export'
```

For inline requirements, write the exact request to a temporary file and pass it
as `--source-file /path/to/snapshot --title inline-spec`,
unless the user supplied a stable title. Do not derive the title from a randomly
named temporary file: repeated identical requests must resolve to the same run
identity. Keep the source file until initialization completes. The helper snapshots
source bytes before switching branches and saves them unchanged as `source.md`.
It does not rewrite the input. A tracked input can disappear when Git switches
to a base that lacks it; the saved snapshot remains available for resume.

## Inputs and identity

All flags take exactly one value. `--source-file` is mandatory. Optional flags:

| Flag | Meaning |
| --- | --- |
| `--title` | Human title for the branch slug; defaults to source basename without `.md`. |
| `--issue` | Positive issue number, used as run ID. |
| `--base-ref` | Explicit base branch, overriding configuration; accepted origin/ref prefixes are normalized. |
| `--issue-base` | Parsed issue-body base, used when config has no base. |
| `--label-base` | Parsed issue-label base, used after issue-body fallback. |
| `--branch` | Explicit feature branch; must be under `feat/`. |
| `--run-id` | Select existing persisted metadata for resume; never creates a new identity. |

Without an explicit base, precedence is config `base_ref`, issue body, issue
label, then `main`. Accept a branch name such as `main`, `origin/main`,
`refs/heads/main`, or `refs/remotes/origin/main`; store each as `main` in
`base_ref`, suitable for PR base selection and `origin/<base_ref>` comparisons.
Branch names containing slashes, such as `release/next`, remain supported.
Commit IDs, revision expressions, tags, and other ref namespaces are not base
branches. Require an exact local branch ref, or an existing local `origin`
remote-tracking ref whose branch still exists on origin. Prefer the local branch
when both exist. Fetch separately if the needed ref is missing or stale; the
initializer never fetches implicitly. Checkout uses the qualified local ref while
metadata always stores the normalized branch name. The legacy CI resolver is
unchanged by this interactive helper.

The normalized slug is lowercase ASCII, punctuation collapsed to hyphens,
trimmed, and limited to 40 characters; an empty slug becomes `spec`. File/inline
run IDs are `<slug>-<first-eight-sha256-hex>` and branches `feat/<run-id>`. Issue
run IDs are the issue number and branches `feat/<issue>-<slug>`.

The helper does not implicitly consume CI environment variables. Controllers
translate validated supplied context into explicit flags. Existing metadata is
required to reuse any existing branch, including one supplied explicitly.

## Preflight and persistence

Before creating a branch or run directory, require an attached Git worktree,
reachable `origin`, an available base branch as described above, a clean tracked worktree and index,
and no local or remote branch collision. Untracked files, including the source,
are allowed; Git still refuses checkout if it would overwrite an untracked file.
Existing run directories without metadata and symlinked run storage are rejected.
No reset, forced branch creation, stash, commit, push, or remote mutation occurs.

The helper creates `.agentic-loop/<run-id>/source.md` and `run-context.json`.
Metadata includes schema version `1`, run ID/directory, absolute source path,
SHA-256 source hash, branch, base, and optional issue. Stdout adds `resumed` to
that metadata. Persist these artifacts using the existing controller commit/push
workflow; do not interpret successful initialization as persisted remote state.
State and immutable invocation requirements remain controller-owned.

Resume requires the matching feature branch already checked out, unchanged source
bytes, a matching saved snapshot, and reachable origin/base. Pass the saved
`source.md` as input when the original is no longer available, together with
`--run-id`. Explicit branch/base/issue values must match metadata; equivalent base
prefixes are normalized before comparison. Initialization
never rewrites metadata or requirements on resume and permits tracked changes
from unfinished work. The controller must preserve persisted requirements and
ask the user to choose a run if its request matches multiple runs; the helper
never guesses between persisted directories.

After unexpected filesystem errors during creation, the branch or partial run
may exist. Inspect and recover explicitly; the helper deliberately refuses to
reset or overwrite it on retry.

Run integration tests with:

```bash
python3 skills/agentic-loop/scripts/__tests__/test_init_run.py
```
