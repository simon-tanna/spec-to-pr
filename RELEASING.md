# Releasing `spec-to-pr`

This plugin is distributed from its own repository: `.claude-plugin/plugin.json`
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

1. Update `CHANGELOG.md` — move `Unreleased` to the new version with a date.
2. Bump the version in **both** files (keep identical):
   - `.claude-plugin/plugin.json` → `"version"`
   - `.claude-plugin/marketplace.json` → the `spec-to-pr` entry's `"version"`
3. Validate:
   ```bash
   claude plugin validate .
   jq . .claude-plugin/plugin.json .claude-plugin/marketplace.json
   ```
4. Commit, tag, push:
   ```bash
   git add -A
   git commit -m "Release vX.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```
5. (Optional) Cut a GitHub Release from the tag using the CHANGELOG section.

## How users update

```bash
/plugin marketplace update            # refresh the marketplace catalog
/plugin update spec-to-pr             # update the installed plugin
```

Marketplace-catalog refresh and installed-plugin update are separate steps.
