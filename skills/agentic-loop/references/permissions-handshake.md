# Permission-Grant Handshake

Used when a CI run is blocked by a missing tool permission. Same shape as
`Interview Handshake` (ci-mode.md §38) but for tool grants instead of spec
ambiguities.

## Issue-comment template

```
🛑 **Loop paused — missing permission**

Stage: <stage> · Issue: #<issue> · Branch: `<branch>`

The skill needs the **`<ToolName>`** tool but it is not in the workflow's
`--allowed-tools` list (or `additional_permissions:` for action-level perms).

**Why it was needed:** <one-sentence reason captured from the subagent's prior thinking>

**To grant and resume:**
1. Edit `.github/workflows/claude.yml` and add `<ToolName>` to the
   `--allowed-tools` flag in `claude_args`.
2. Commit and push to your default branch (the branch the workflow runs from).
3. Reply on this issue with `@claude resume` to retrigger the loop.

If the permission should NOT be granted, reply with `@claude skip <ToolName>`
and the skill will mark the originating task as `BLOCKED` and escalate.
```

## Reply parsing

- `@claude resume` → on the next run, verify the permission is actually granted **before** re-attempting the original call: dry-run-probe by attempting a low-cost form of the tool (e.g. a `--help` or schema-only invocation). If the probe still returns `tool_use_error: ... permissions ...`, the workflow change did not land — post a follow-up comment ("permission still denied after `@claude resume`; the workflow may need redeploying") and exit. Only if the probe succeeds, retry the original call and continue from the saved checkpoint. This prevents looping on the same denial when the workflow has not picked up the new `--allowed-tools` list.
- `@claude skip <ToolName>` → mark blocker resolved, escalate the task that
  needed it through normal `BLOCKED` handling.
