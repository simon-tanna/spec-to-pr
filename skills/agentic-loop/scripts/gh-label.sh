#!/usr/bin/env bash
# Idempotent label toggle for the agentic-loop state machine.
# Usage: gh-label.sh <add|remove> <issue-number> <label>

set -euo pipefail

ACTION="${1:?add|remove required}"
ISSUE="${2:?issue number required}"
LABEL="${3:?label required}"

case "$ACTION" in
  add)
    gh issue edit "$ISSUE" --add-label "$LABEL" >/dev/null
    ;;
  remove)
    # Do not fail if the label isn't present.
    gh issue edit "$ISSUE" --remove-label "$LABEL" >/dev/null 2>&1 || true
    ;;
  *)
    echo "unknown action: $ACTION (expected add|remove)" >&2
    exit 1
    ;;
esac

echo "label $ACTION: #$ISSUE $LABEL"
