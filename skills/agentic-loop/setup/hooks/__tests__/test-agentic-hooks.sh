#!/usr/bin/env bash
# Smoke tests for the four agentic-loop gate hooks.
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
TDD_TRACE="$HOOKS/agentic-loop-check-tdd-trace.sh"

[ -x "$TASKS_JSON" ]  || { echo "missing $TASKS_JSON"; exit 1; }
[ -x "$STATE_TRANS" ] || { echo "missing $STATE_TRANS"; exit 1; }
[ -x "$PR_READY" ]    || { echo "missing $PR_READY"; exit 1; }
[ -x "$TDD_TRACE" ]   || { echo "missing $TDD_TRACE"; exit 1; }
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
echo "== state-transition hook: spec→plan gate =="

# Stage 1 → 2 preconditions: spec.md + approved JSON spec-review.md + no open questions.
echo "stub spec" > .agentic-loop/99/spec.md
rm -f .agentic-loop/99/spec-review.md .agentic-loop/99/open-questions.md

# P1: .state=plan with no spec-review.md → block
run_case "P1: .state=plan, no spec-review.md" 2 "$STATE_TRANS" "$(mk_state_write_payload "plan")"

# P2: spec-review verdict needs-changes → block
echo '{"verdict":"needs-changes","force_interview":true,"critical":[],"important":[{"x":1}]}' > .agentic-loop/99/spec-review.md
run_case "P2: .state=plan, spec-review needs-changes" 2 "$STATE_TRANS" "$(mk_state_write_payload "plan")"

# P3: approved + force_interview false + no open questions → allow
echo '{"verdict":"approved","force_interview":false,"critical":[],"important":[]}' > .agentic-loop/99/spec-review.md
run_case "P3: .state=plan, approved spec-review" 0 "$STATE_TRANS" "$(mk_state_write_payload "plan")"

# P4: approved but open-questions.md non-empty → block
echo "Q1 unanswered" > .agentic-loop/99/open-questions.md
run_case "P4: .state=plan, approved but open questions" 2 "$STATE_TRANS" "$(mk_state_write_payload "plan")"
rm -f .agentic-loop/99/open-questions.md

# P5: entering spec is always a free pass (regression) → allow
run_case "P5: .state=spec free pass" 0 "$STATE_TRANS" "$(mk_state_write_payload "spec")"

echo ""
echo "== pr-ready hook =="

# Scenario 9: gh pr create with one task at blocker_count 2 → block
echo "$TASK_CLEAN" | jq '.tasks[0].blocker_count = 2' > .agentic-loop/99/tasks.json
AGENTIC_ISSUE=99 run_case "9: gh pr create, task blocker_count 2" 2 "$PR_READY" "$(mk_pr_create_payload)"

# Bonus: pr-ready with clean tasks → allow
echo "$TASK_CLEAN" > .agentic-loop/99/tasks.json
AGENTIC_ISSUE=99 run_case "9b: gh pr create, all clean" 0 "$PR_READY" "$(mk_pr_create_payload)"

echo ""
echo "== tdd-trace hook =="

# This hook inspects real commits, so stand up a throwaway git repo in the
# sandbox (cwd already == sandbox, which contains .agentic-loop/).
if git init -q 2>/dev/null; then
  GIT="git -c user.email=t@t -c user.name=t -c commit.gpgsign=false"

  # Good commit: test file present + TDD: line in the message body.
  printf 'test\n' > foo.test.ts
  printf 'impl\n'  > foo.ts
  $GIT add foo.test.ts foo.ts
  $GIT commit -q -m "feat(foo): add foo" -m "TDD: foo.test.ts:1-5 written before implementation"
  SHA_GOOD=$($GIT rev-parse HEAD)

  # Bad commit: implementation only — no test file, no TDD: line.
  printf 'impl2\n' > bar.ts
  $GIT add bar.ts
  $GIT commit -q -m "feat(bar): add bar"
  SHA_BAD=$($GIT rev-parse HEAD)

  mk_done_tasks() { # $1 = commit sha
    jq -n --arg s "$1" '{tasks:[{id:"T1",status:"done",commit_sha:$s,spec_review_sha:"a",quality_review_sha:"b"}]}'
  }

  # T1: done task whose commit has test + TDD: line → allow
  run_case "T1: done, commit has test + TDD line" 0 "$TDD_TRACE" "$(mk_write_payload "$(mk_done_tasks "$SHA_GOOD")")"

  # T2: done task whose commit lacks test + TDD: line → block
  run_case "T2: done, commit missing test + TDD line" 2 "$TDD_TRACE" "$(mk_write_payload "$(mk_done_tasks "$SHA_BAD")")"

  # T3: done task with empty commit_sha → allow (presence-only, non-flaky)
  run_case "T3: done, empty commit_sha" 0 "$TDD_TRACE" "$(mk_write_payload "$(mk_done_tasks "")")"

  # T4: done task with a sha not in the repo → allow
  run_case "T4: done, unresolvable commit_sha" 0 "$TDD_TRACE" "$(mk_write_payload "$(mk_done_tasks "0000000000000000000000000000000000000000")")"

  # T5: Edit fragment sets done + bad commit_sha → block
  run_case "T5: Edit done + bad commit_sha" 2 "$TDD_TRACE" "$(mk_edit_payload "\"status\": \"done\", \"commit_sha\": \"$SHA_BAD\"")"

  # T6: non-tasks.json write is ignored → allow
  run_case "T6: non-tasks.json write ignored" 0 "$TDD_TRACE" "$(jq -n '{tool_name:"Write",tool_input:{file_path:".agentic-loop/99/spec.md",content:"x"}}')"
else
  echo "  (skipped — git init unavailable)"
fi

echo ""
echo "==========================="
printf 'passed: %d   failed: %d\n' "$PASS" "$FAIL"
if [ "$FAIL" -gt 0 ]; then
  printf 'failed scenarios:\n'
  for n in "${FAILED_NAMES[@]}"; do printf '  - %s\n' "$n"; done
  exit 1
fi
echo "all scenarios passed"
