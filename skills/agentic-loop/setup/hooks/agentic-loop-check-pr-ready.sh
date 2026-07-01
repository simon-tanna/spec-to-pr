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

REASONS=()

if [ -s "$DIR/tasks.json" ]; then
  JQ_ERR=$(mktemp)
  JQ_STATUS=0
  OFFENDERS=$(jq -r '
    .tasks // []
    | map(select(.status != "done"
        or (.spec_review_sha // "") == ""
        or (.quality_review_sha // "") == ""
        or (.blocker_count // 0) >= 2))
    | .[].id
  ' "$DIR/tasks.json" 2>"$JQ_ERR") || JQ_STATUS=$?

  if [ "$JQ_STATUS" -ne 0 ]; then
    REASONS+=("$DIR/tasks.json failed to parse (jq exit $JQ_STATUS):")
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      REASONS+=("    $line")
    done < "$JQ_ERR"
  elif [ -n "$OFFENDERS" ]; then
    REASONS+=("incomplete tasks in $DIR/tasks.json:")
    while IFS= read -r id; do
      [ -z "$id" ] && continue
      REASONS+=("    • $id")
    done <<< "$OFFENDERS"
  fi

  rm -f "$JQ_ERR"
else
  REASONS+=("$DIR/tasks.json missing or empty")
fi

if [ -f "$DIR/open-questions.md" ] && [ -s "$DIR/open-questions.md" ]; then
  REASONS+=("$DIR/open-questions.md is non-empty — interview not closed")
fi

[ ${#REASONS[@]} -eq 0 ] && exit 0

{
  echo "Blocked by agentic-loop PR-ready gate."
  echo ""
  echo "Cannot \`gh pr create\` for $DIR. Reasons:"
  for r in "${REASONS[@]}"; do
    echo "  • $r"
  done
  echo ""
  echo "Finish all tasks (status:done, both review shas populated, and"
  echo "blocker_count < 2 — reset by plan-loop revision if it ever hit 2),"
  echo "and resolve any open questions before opening the PR."
  echo "See the agentic-loop skill's SKILL.md §Stage 4 and"
  echo "the agentic-loop skill's references/status-handling.md."
} >&2
exit 2
