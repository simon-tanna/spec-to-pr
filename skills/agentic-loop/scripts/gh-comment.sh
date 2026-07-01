#!/usr/bin/env bash
# Post a comment to a GitHub issue or PR.
# Usage: gh-comment.sh <issue-number> <body-file-or-dash-for-stdin>
# Requires: gh CLI authenticated via workflow token or personal token.

set -euo pipefail

ISSUE="${1:?issue number required}"
BODY_SOURCE="${2:?body file or '-' for stdin required}"

if [ "$BODY_SOURCE" = "-" ]; then
  BODY="$(cat)"
else
  [ -f "$BODY_SOURCE" ] || { echo "body file not found: $BODY_SOURCE" >&2; exit 1; }
  BODY="$(cat "$BODY_SOURCE")"
fi

# Tag issue author so they get notified. AGENTIC_AUTHOR exported by workflow pin step.
# Skip if unset (interactive use), empty, or already present in body.
if [ -n "${AGENTIC_AUTHOR:-}" ] && ! printf '%s' "$BODY" | grep -qF "@${AGENTIC_AUTHOR}"; then
  BODY="@${AGENTIC_AUTHOR} ${BODY}"
fi

# gh issue comment works for both issues and PRs since PRs are issues at the API level.
printf '%s\n' "$BODY" | gh issue comment "$ISSUE" --body-file -
