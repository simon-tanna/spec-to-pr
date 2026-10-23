#!/usr/bin/env bash
# PreToolUse hook — agentic-loop PR-ready gate.
# Block `gh pr create` while any task is incomplete or any review sha
# is missing. Backstop before ship.
#
# Out-of-loop `gh pr create` (no .agentic-loop/, no $AGENTIC_BRANCH)
# passes through unchanged.

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

[ "$TOOL_NAME" = "Bash" ] || exit 0

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Match `gh pr create` as a whole-word command (any flags/positional args).
echo "$CMD" | grep -qE '(^|[[:space:];|&])gh[[:space:]]+pr[[:space:]]+create([[:space:]]|$)' || exit 0

# If we're not running inside an agentic-loop run, the hook is inert.
[ -d .agentic-loop ] || exit 0

# Pick the active issue dir. Prefer $AGENTIC_ISSUE; fall back to a single
# directory under .agentic-loop/.
if [ -n "${AGENTIC_ISSUE:-}" ] && [ -d ".agentic-loop/$AGENTIC_ISSUE" ]; then
  DIR=".agentic-loop/$AGENTIC_ISSUE"
else
  COUNT=$(find .agentic-loop -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
  if [ "$COUNT" -ne 1 ]; then
    # Cannot disambiguate; let the call through rather than block spuriously.
    exit 0
  fi
  DIR=$(find .agentic-loop -mindepth 1 -maxdepth 1 -type d | head -n1)
fi

# Policies are shipped alongside wrappers for standalone hook installations.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib-gates.sh"
gate_pr_ready "$DIR"
