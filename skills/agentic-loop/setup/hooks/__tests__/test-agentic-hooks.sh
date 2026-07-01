#!/usr/bin/env bash
# Smoke tests for the three agentic-loop hooks.
# Runs all hooks against synthetic PreToolUse payloads and verifies exit
# codes match expectations. No git mutations; uses a temp .agentic-loop/
# tree which is cleaned up at exit.
#
# Usage: bash setup/hooks/__tests__/test-agentic-hooks.sh
# Exit:  0 if all scenarios pass; non-zero with diagnostic on first failure.

set -uo pipefail

# The hooks under test live in this test file's parent directory.
HOOKS="$(cd "$(dirname "$0")/.." && pwd)"

TASKS_JSON="$HOOKS/agentic-loop-check-tasks-json.sh"
STATE_TRANS="$HOOKS/agentic-loop-check-state-transition.sh"
PR_READY="$HOOKS/agentic-loop-check-pr-ready.sh"

[ -x "$TASKS_JSON" ]  || { echo "missing $TASKS_JSON"; exit 1; }
[ -x "$STATE_TRANS" ] || { echo "missing $STATE_TRANS"; exit 1; }
[ -x "$PR_READY" ]    || { echo "missing $PR_READY"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq required"; exit 1; }

# Hooks short-circuit when .agentic-loop/ does not exist in cwd; the
# state-transition + pr-ready hooks also read tasks.json from disk. We
# stand up a sandbox under a temp dir and cd into it.
SANDBOX=$(mktemp -d)
trap 'cd / >/dev/null; rm -rf "$SANDBOX"' EXIT
cd "$SANDBOX"
mkdir -p .agentic-loop/99

PASS=0
FAIL=0
FAILED_NAMES=()

run_case() {
  local name="$1" expect="$2" hook="$3" payload="$4"
  local got
  got=$(printf '%s' "$payload" | bash "$hook" >/dev/null 2>&1; echo $?)
  if [ "$got" = "$expect" ]; then
    printf '  ✓ %s\n' "$name"
    PASS=$((PASS + 1))
  else
    printf '  ✗ %s (expected exit=%s, got exit=%s)\n' "$name" "$expect" "$got"
    FAIL=$((FAIL + 1))
    FAILED_NAMES+=("$name")
  fi
}

# Helper: builds a Write tool_input payload for tasks.json
mk_write_payload() {
  local content="$1"
  jq -n --arg c "$content" \
    '{tool_name:"Write", tool_input:{file_path:".agentic-loop/99/tasks.json", content:$c}}'
}

mk_edit_payload() {
  local new_string="$1"
  jq -n --arg n "$new_string" \
    '{tool_name:"Edit", tool_input:{file_path:".agentic-loop/99/tasks.json", new_string:$n}}'
}

mk_state_write_payload() {
  local content="$1"
  jq -n --arg c "$content" \
    '{tool_name:"Write", tool_input:{file_path:".agentic-loop/99/.state", content:$c}}'
}

mk_pr_create_payload() {
  jq -n '{tool_name:"Bash", tool_input:{command:"gh pr create --title x --body y"}}'
}

echo "== tasks-json hook =="

# Scenario 1: clean done, both shas, blocker_count 0 → allow
TASK_CLEAN='{"tasks":[{"id":"T1","status":"done","spec_review_sha":"abc","quality_review_sha":"def","blocker_count":0}]}'
run_case "1: clean done, blocker_count 0" 0 "$TASKS_JSON" "$(mk_write_payload "$TASK_CLEAN")"

# Scenario 2: done with blocker_count 2 → block
TASK_BLOCKED='{"tasks":[{"id":"T1","status":"done","spec_review_sha":"abc","quality_review_sha":"def","blocker_count":2}]}'
run_case "2: done with blocker_count 2" 2 "$TASKS_JSON" "$(mk_write_payload "$TASK_BLOCKED")"

# Scenario 3: done with blocker_count field absent → allow (// 0 default)
TASK_NO_FIELD='{"tasks":[{"id":"T1","status":"done","spec_review_sha":"abc","quality_review_sha":"def"}]}'
run_case "3: done, no blocker_count field" 0 "$TASKS_JSON" "$(mk_write_payload "$TASK_NO_FIELD")"

# Scenario 4: Edit fragment sets status=done with both shas, no blocker_count → allow
EDIT_NO_BLOCKER='"status": "done", "spec_review_sha": "abc", "quality_review_sha": "def"'
run_case "4: Edit done + shas, no blocker_count in fragment" 0 "$TASKS_JSON" "$(mk_edit_payload "$EDIT_NO_BLOCKER")"

# Scenario 5: Edit fragment with explicit blocker_count: 0 → allow
EDIT_BC_ZERO='"status": "done", "spec_review_sha": "abc", "quality_review_sha": "def", "blocker_count": 0'
run_case "5: Edit done + shas + blocker_count 0" 0 "$TASKS_JSON" "$(mk_edit_payload "$EDIT_BC_ZERO")"

# Scenario 6: Edit fragment with blocker_count: 5 → block
EDIT_BC_HIGH='"status": "done", "spec_review_sha": "abc", "quality_review_sha": "def", "blocker_count": 5'
run_case "6: Edit done + shas + blocker_count 5" 2 "$TASKS_JSON" "$(mk_edit_payload "$EDIT_BC_HIGH")"

# Scenario 10 (regression): Edit fragment setting status=done without spec_review_sha → block
EDIT_MISSING_SHA='"status": "done", "quality_review_sha": "def"'
run_case "10: regression — done without spec_review_sha" 2 "$TASKS_JSON" "$(mk_edit_payload "$EDIT_MISSING_SHA")"

echo ""
echo "== state-transition hook =="

# Stand up artefacts for the 'done' transition gate: plan.md, plan-review.md,
# and tasks.json must all be in place; we vary tasks.json to test blocker_count.
echo "stub plan" > .agentic-loop/99/plan.md
echo "stub plan review" > .agentic-loop/99/plan-review.md

# Scenario 7: .state=done while a task has blocker_count: 3 → block
echo "$TASK_CLEAN" | jq '.tasks[0].blocker_count = 3' > .agentic-loop/99/tasks.json
run_case "7: .state=done with task blocker_count 3" 2 "$STATE_TRANS" "$(mk_state_write_payload "done")"

# Scenario 8: .state=done with all tasks clean → allow
echo "$TASK_CLEAN" > .agentic-loop/99/tasks.json
run_case "8: .state=done all clean" 0 "$STATE_TRANS" "$(mk_state_write_payload "done")"

echo ""
echo "== pr-ready hook =="

# Scenario 9: gh pr create with one task at blocker_count 2 → block
echo "$TASK_CLEAN" | jq '.tasks[0].blocker_count = 2' > .agentic-loop/99/tasks.json
AGENTIC_ISSUE=99 run_case "9: gh pr create, task blocker_count 2" 2 "$PR_READY" "$(mk_pr_create_payload)"

# Bonus: pr-ready with clean tasks → allow
echo "$TASK_CLEAN" > .agentic-loop/99/tasks.json
AGENTIC_ISSUE=99 run_case "9b: gh pr create, all clean" 0 "$PR_READY" "$(mk_pr_create_payload)"

echo ""
echo "==========================="
printf 'passed: %d   failed: %d\n' "$PASS" "$FAIL"
if [ "$FAIL" -gt 0 ]; then
  printf 'failed scenarios:\n'
  for n in "${FAILED_NAMES[@]}"; do printf '  - %s\n' "$n"; done
  exit 1
fi
echo "all scenarios passed"
