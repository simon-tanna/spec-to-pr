# PR Body

The PR body is whatever `"${AGENTIC_SKILL_DIR}/scripts/render-pr-body.sh" <run-id>` prints; it reads `tasks.json`, `spec.md` and `plan.md`, so the body always matches committed state. To change the body, edit the script. Under the GitHub adapter, Stage 4 pipes it into `gh pr create`:

```bash
"${AGENTIC_SKILL_DIR}/scripts/render-pr-body.sh" "$AGENTIC_ISSUE" \
  | gh pr create --base "$AGENTIC_BASE_REF" --title "<title>" --body-file -
```

Always pass `--base "$AGENTIC_BASE_REF"`. The workflow's pin step sets it from config `base_ref`, then the issue's `Base branch` field, then a `base:<ref>` label, then `main`.
