# Releasing `spec-to-pr`

The skills suite is installed directly from this GitHub repository with
`pnpm dlx skills add simon-tanna/spec-to-pr`. Commit all generated resource copies;
users do not run a build and no npm publication is needed.

The optional Claude plugin is distributed from the same repository: `.claude-plugin/plugin.json`
is the manifest and `.claude-plugin/marketplace.json` is a single-plugin
marketplace with `source: "./"`.

## How versioning works here

- **`plugin.json.version` is the single source of truth.** Claude Code resolves
  a plugin's version from `plugin.json` first, then the marketplace entry, then
  the git commit SHA. If `version` is set in *both* `plugin.json` and
  `marketplace.json`, **`plugin.json` wins silently** — so keep them identical to
  avoid confusion.
- **The version string drives updates.** With `source: "./"`, users only receive
  an update when the version string changes. **You must bump the version to ship
  an update** — pushing commits without a bump leaves users on the cached version.
- **Semantic versioning:** `MAJOR.MINOR.PATCH` (breaking / feature / fix).
  Pre-release: `0.2.0-beta.1`, `-rc.1`. Pre-1.0 (`0.x`) signals a stabilizing API.
- **Git tags** (`vX.Y.Z`) are not consumed by Claude Code for a `source: "./"`
  plugin — they are the human/GitHub-Release anchor. Tag every release anyway.

## Release checklist

1. Review user docs for anything added this release — a new flag, config key, or capability should
   reach `README.md`, the relevant skill `setup/SETUP.md`, and `CHANGELOG.md`, not just the skill's
   internal `references/`.
2. Update `CHANGELOG.md` — move `Unreleased` to the new version with a date.
3. Bump the version in **both** files (keep identical):
   - `.claude-plugin/plugin.json` → `"version"`
   - `.claude-plugin/marketplace.json` → the `spec-to-pr` entry's `"version"`
4. Run `python3 scripts/build-distribution.py`, then
   `python3 scripts/build-distribution.py --check`. Verify the loop contains its validation workflow and
   every skill contains its role/dispatch resources without sibling dependencies.
5. Validate isolated Skills CLI installations from the proposed release checkout:
   list exactly three public skills; install each alone and the whole suite for
   Codex and Claude in disposable directories, in default and `--copy` modes.
   Verify bundled resources after making the source checkout unavailable. Never
   use global installation for these release tests.
6. Run packaging/generation tests, initialization integration tests, shared-gate
   tests, and existing hook/nudge regressions. Record test results separately from
   live-harness evidence. Require recorded fresh-child delegation, interactive
   question/answer pause and resume, negative gate cases, and a complete fixture
   run for each claimed harness. Missing credentials or an unavailable harness
   leave acceptance incomplete; they are not passing evidence. Existing headless
   CI remains Claude-only.
7. Validate Claude manifests:
   ```bash
   claude plugin validate .
   jq . .claude-plugin/plugin.json .claude-plugin/marketplace.json
   ```
8. After acceptance and release authorization, commit, tag, push:
   ```bash
   git add -A
   git commit -m "Release vX.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```
9. (Optional) Cut a GitHub Release from the tag using the CHANGELOG section.

## Evaluation tools and evidence

Run `bash scripts/test.sh` for offline regressions, including dispatch evidence
parser tests. Maintained opt-in evaluators live in `scripts/evals/`:

```bash
python3 scripts/evals/test_skills_install.py --allow-network
python3 scripts/evals/run_portable_dispatch_smoke.py --harness codex --output /tmp/spec-to-pr-live-codex
python3 scripts/evals/run_portable_dispatch_smoke.py --harness claude --output /tmp/spec-to-pr-live-claude
```

The installation evaluator uses disposable projects and requires network access.
The dispatch evaluator uses existing harness authentication and writes traces to
its explicit output directory. These live evaluations are separate from the
offline suite.

Recorded 0.3.0 evidence and remaining acceptance gaps are in
[the validation record](docs/validation/0.3.0/portability-validation.md).
Historical local experiments belong in the ignored
`skills/agentic-loop-workspace/` directory; keep maintained tools and release
evidence outside that workspace.

## How users update

Skills installations use the Skills CLI's update command. From the target project:

```bash
pnpm dlx skills update -p -y
```

For global skills, use `pnpm dlx skills update -g -y`. Plugin manifests do not
register native agents or hooks for a Skills CLI installation.

Claude plugin installations use:


```bash
/plugin marketplace update            # refresh the marketplace catalog
/plugin update spec-to-pr             # update the installed plugin
```

Marketplace-catalog refresh and installed-plugin update are separate steps.
