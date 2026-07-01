#!/usr/bin/env bash
# PreToolUse hook — agentic-loop tasks.json gate.
# Block Write/Edit on .agentic-loop/<id>/tasks.json that marks any task
# status:"done" without populated spec_review_sha AND quality_review_sha.
#
# Why: the loop's quality story rests on per-task two-stage review (spec-
# compliance + code-quality). The model has skipped this in past CI runs
# to conserve turns. Hook makes the skip impossible.
#
# Pairs with .claude/skills/agentic-loop/SKILL.md §Stage 3.

set -euo pipefail

# Project-scope guard: inert outside loop runs.
[ -d .agentic-loop ] || exit 0

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

[[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" ]] || exit 0

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only inspect tasks.json under .agentic-loop/<id>/
[[ "$FILE_PATH" =~ \.agentic-loop/[^/]+/tasks\.json$ ]] || exit 0

if [[ "$TOOL_NAME" == "Write" ]]; then
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')

  # Validate JSON; if it doesn't parse let the actual write fail naturally.
  echo "$CONTENT" | jq empty >/dev/null 2>&1 || exit 0

  OFFENDERS=$(echo "$CONTENT" | jq -r '
    .tasks // []
    | map(select(.status == "done"
        and ((.spec_review_sha // "") == ""
             or (.quality_review_sha // "") == ""
             or (.blocker_count // 0) >= 2)))
    | .[].id
  ')

  if [ -n "$OFFENDERS" ]; then
    {
      echo "Blocked by agentic-loop tasks.json gate."
      echo ""
      echo "These tasks are marked status:\"done\" with one or more gate failures:"
      while IFS= read -r id; do
        [ -z "$id" ] && continue
        echo "  • $id"
      done <<< "$OFFENDERS"
      echo ""
      echo "Possible causes:"
      echo "  • spec_review_sha or quality_review_sha missing/empty —"
      echo "    run the missing review pass via code-reviewer."
      echo "  • blocker_count >= 2 — the task hit BLOCKED twice and must"
      echo "    round-trip through plan-loop revision (which resets"
      echo "    blocker_count to 0) before reaching done."
      echo ""
      echo "See .claude/skills/agentic-loop/SKILL.md §Stage 3 and"
      echo ".claude/skills/agentic-loop/references/status-handling.md."
    } >&2
    exit 2
  fi
  exit 0
fi

# Edit branch — fragment may not include surrounding fields. Conservative
# rule: any new_string introducing "status": "done" must include both
# review sha keys with non-empty values somewhere in the same fragment.
NEW=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')
[ -z "$NEW" ] && exit 0
echo "$NEW" | grep -qE '"status"\s*:\s*"done"' || exit 0

# Both review-sha keys must appear with non-empty string values in the fragment.
HAS_SPEC=$(echo "$NEW" | grep -cE '"spec_review_sha"\s*:\s*"[^"]+"' || true)
HAS_QUAL=$(echo "$NEW" | grep -cE '"quality_review_sha"\s*:\s*"[^"]+"' || true)

if [ "$HAS_SPEC" -eq 0 ] || [ "$HAS_QUAL" -eq 0 ]; then
  {
    echo "Blocked by agentic-loop tasks.json gate."
    echo ""
    echo "Edit introduces status:\"done\" without both review shas in the"
    echo "same fragment."
    echo ""
    echo "Either:"
    echo "  1. Run spec-compliance + code-quality reviews, populate both"
    echo "     spec_review_sha and quality_review_sha in the same Edit, OR"
    echo "  2. Use Write to overwrite the full tasks.json with the complete"
    echo "     task object including both shas."
    echo ""
    echo "See .claude/skills/agentic-loop/SKILL.md §Stage 3."
  } >&2
  exit 2
fi

# blocker_count check: block ONLY when the fragment explicitly sets
# blocker_count to a value >= 2 alongside status="done". Absence of
# blocker_count from the fragment is allowed (partial edit — the on-disk
# value governs and other hooks read it from disk).
BLOCKER_HIGH=$(echo "$NEW" | grep -cE '"blocker_count"\s*:\s*([2-9]|[1-9][0-9]+)([^0-9]|$)' || true)

if [ "$BLOCKER_HIGH" -gt 0 ]; then
  {
    echo "Blocked by agentic-loop tasks.json gate."
    echo ""
    echo "Edit sets status:\"done\" while explicitly setting blocker_count >= 2."
    echo "A task that hit BLOCKED twice must round-trip through plan-loop"
    echo "revision (which resets blocker_count to 0) before reaching done."
    echo ""
    echo "See .claude/skills/agentic-loop/references/status-handling.md."
  } >&2
  exit 2
fi

exit 0
