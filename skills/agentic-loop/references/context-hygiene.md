# Context Hygiene

In CI mode the loop must eject before token exhaustion silently truncates a turn between two tool calls. The `PostToolUse` context-check hook (`scripts/postooluse-context-check.sh`) runs every 15 tool calls. When its token estimate passes the model threshold, or the run passes its wall-clock budget (both set in that script), it drops two files:

- `.agentic-loop/eject-flag` — presence signals an eject is due
- `.agentic-loop/eject-reason` — one-line human-readable reason

**At every per-task checkpoint and at the top of every review loop iteration**, check the flag before dispatching a subagent:

```bash
if [ -f ".agentic-loop/eject-flag" ]; then
  REASON=$(cat ".agentic-loop/eject-reason" 2>/dev/null || echo 'estimated token threshold exceeded')
  rm -f ".agentic-loop/eject-flag" ".agentic-loop/eject-reason"
  "${AGENTIC_SKILL_DIR}/scripts/git-sync.sh" checkpoint "chore(loop): context hygiene checkpoint on #${AGENTIC_ISSUE}"

  # Auto-resume config — values flow from GitHub repo variables (Settings →
  # Actions → Variables) into $GITHUB_ENV via the workflow's "Pin agentic-loop
  # branch" step. The skill reads them here with safe fallbacks so local /
  # interactive runs work even when the env is not set. See
  # auto-resume-config.md for the single source of truth.
  RESUME_CAP="${AGENTIC_RESUME_CAP:-10}"
  MARKER="${AGENTIC_RESUME_MARKER:-AGENTIC-LOOP-AUTO-RESUME}"
  ATTEMPTS_FILE=".agentic-loop/${AGENTIC_ISSUE}/resume-attempts"
  ATTEMPTS=0
  [ -f "$ATTEMPTS_FILE" ] && ATTEMPTS=$(cat "$ATTEMPTS_FILE" 2>/dev/null || echo 0)
  ATTEMPTS=$((ATTEMPTS + 1))
  printf '%d' "$ATTEMPTS" > "$ATTEMPTS_FILE"
  "${AGENTIC_SKILL_DIR}/scripts/git-sync.sh" commit "chore(loop): context eject for #${AGENTIC_ISSUE} (resume-attempts ${ATTEMPTS})"

  if [ "$ATTEMPTS" -le "$RESUME_CAP" ]; then
    MSG=$(printf 'agentic-loop: context threshold reached — ejecting for hygiene (attempt %d/%d).\nAll state is committed. Resuming automatically on next trigger.\nReply `@claude stop` at any time to halt.\n<!-- %s issue=#%s attempt=%d/%d -->' \
      "$ATTEMPTS" "$RESUME_CAP" "$MARKER" "$AGENTIC_ISSUE" "$ATTEMPTS" "$RESUME_CAP")
  else
    MSG=$(printf 'agentic-loop: auto-resume cap reached (%d/%d). All state is committed on branch `%s`.\ncc @%s — reply `@claude continue` to resume manually.' \
      "$RESUME_CAP" "$RESUME_CAP" "${AGENTIC_BRANCH:-unknown}" "${AGENTIC_AUTHOR:-human}")
  fi
  printf '%s\n' "$MSG" | "${AGENTIC_SKILL_DIR}/scripts/notify.sh" blocked "$AGENTIC_ISSUE" -
  exit 0
fi
```

On the next CI trigger the loop reads `.state` and `tasks.json` from the committed branch and resumes exactly where it left off. When the auto-resume marker is present the workflow's `if:` branch fires on the bot's own comment, so resumption is automatic without human intervention (up to `RESUME_CAP` consecutive resumes per branch — see `auto-resume-config.md`).

The `PreCompact` hook (`scripts/precompact-flush.sh`) runs `git-sync.sh checkpoint` before any auto- or manual compaction as an independent safety net — the "state in git before reset" invariant is satisfied even if the 15-turn check did not trip first.

The hook reads the model from `CLAUDE_MODEL`, which the workflow stamps. Its turn counter (`.agentic-loop/turn-counter`) is uncommitted, so it restarts with each CI run. Auto-resume identity, cap and marker live in `auto-resume-config.md`.
