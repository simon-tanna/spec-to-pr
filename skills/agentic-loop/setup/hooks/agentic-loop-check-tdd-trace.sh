#!/usr/bin/env bash
# PreToolUse hook — agentic-loop TDD-trace gate.
# Block Write/Edit on .agentic-loop/<id>/tasks.json that marks a task
# status:"done" whose commit does NOT contain a test file AND a `TDD:` line
# in its message body.
#
# Why: the TDD Iron Law (references/tdd.md) is enforced test-first at
# implementer runtime, then RECORDED via a `TDD:` line in the atomic
# per-task commit — red→green is deliberately NOT reconstructable from git
# history because commits are atomic (one task = one green commit). That
# leaves the `TDD:` trace model-verified only: an implementer could mark a
# task done with no test in the commit at all. This hook is the cheap
# deterministic backstop — it verifies PRESENCE (a test path is in the
# commit diff, and a `TDD:` line is in the message). It intentionally does
# NOT try to prove ordering from history; that check was removed on purpose.
#
# Contract: only tasks with a resolvable commit_sha are checked. A done task
# with an empty/unresolvable commit_sha passes here (the tasks-json gate and
# the two-stage review own that case) so the hook never blocks on git
# flakiness — it only ever exits 0 (allow) or 2 (block).
#
# Pairs with the agentic-loop skill's references/tdd.md and SKILL.md §Stage 3.

set -euo pipefail

# Project-scope guard: inert outside loop runs.
[ -d .agentic-loop ] || exit 0

# Test-path signature (aligned with references/tdd.md conventions):
# *.test.* / *.spec.* / *_test.* / *_spec.* / __tests__/ / tests?/ / test_*
TEST_PATH_RE='(\.test\.|\.spec\.|_test\.|_spec\.|/__tests__/|(^|/)tests?/|(^|/)test_)'

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

[[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" ]] || exit 0

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[[ "$FILE_PATH" =~ \.agentic-loop/[^/]+/tasks\.json$ ]] || exit 0

# Verify one commit: prints nothing if OK, else prints the reason(s).
# $1 = commit sha. Only called for non-empty, resolvable shas.
commit_trace_problems() {
  local sha="$1" problems=""
  local body files
  body=$(git show -s --format=%B "$sha" 2>/dev/null || true)
  files=$(git show --name-only --format='' "$sha" 2>/dev/null || true)

  echo "$body" | grep -qE '(^|[^A-Za-z])TDD:' || problems+="no \`TDD:\` line in commit message; "
  echo "$files" | grep -qE "$TEST_PATH_RE" || problems+="no test file in commit diff; "

  printf '%s' "$problems"
}

# Resolve a sha to a commit object; empty/unresolvable → return 1 (skip).
resolvable() {
  local sha="$1"
  [ -n "$sha" ] || return 1
  git cat-file -e "${sha}^{commit}" 2>/dev/null || return 1
}

if [[ "$TOOL_NAME" == "Write" ]]; then
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
  # If it doesn't parse, let the real write fail naturally.
  echo "$CONTENT" | jq empty >/dev/null 2>&1 || exit 0

  # id \t commit_sha, for every done task.
  DONE_TASKS=$(echo "$CONTENT" | jq -r '
    .tasks // []
    | map(select(.status == "done"))
    | .[] | [.id, (.commit_sha // "")] | @tsv
  ')

  OFFENDERS=""
  while IFS=$'\t' read -r id sha; do
    [ -z "$id" ] && continue
    resolvable "$sha" || continue
    problems=$(commit_trace_problems "$sha")
    [ -n "$problems" ] && OFFENDERS+="  • $id ($sha): ${problems%; }"$'\n'
  done <<< "$DONE_TASKS"

  if [ -n "$OFFENDERS" ]; then
    {
      echo "Blocked by agentic-loop TDD-trace gate."
      echo ""
      echo "These tasks are marked status:\"done\" but their commit fails the"
      echo "TDD-trace check:"
      printf '%s' "$OFFENDERS"
      echo ""
      echo "Every task's atomic commit MUST contain the test file it was written"
      echo "against AND a \`TDD:\` line in the message body citing that test"
      echo "(e.g. 'TDD: __tests__/foo.test.ts:12-30 written before implementation')."
      echo "Re-commit the task with the test included and the TDD: trace, then retry."
      echo ""
      echo "See the agentic-loop skill's references/tdd.md and SKILL.md §Stage 3."
    } >&2
    exit 2
  fi
  exit 0
fi

# Edit branch — conservative: only act when the fragment itself introduces
# status:"done" AND carries a resolvable commit_sha. Partial edits without a
# sha pass (the on-disk Write path / tasks-json gate govern).
NEW=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')
[ -z "$NEW" ] && exit 0
echo "$NEW" | grep -qE '"status"\s*:\s*"done"' || exit 0

SHA=$(echo "$NEW" | grep -oE '"commit_sha"\s*:\s*"[0-9a-fA-F]{7,40}"' | head -1 \
  | grep -oE '[0-9a-fA-F]{7,40}' || true)
resolvable "$SHA" || exit 0

problems=$(commit_trace_problems "$SHA")
if [ -n "$problems" ]; then
  {
    echo "Blocked by agentic-loop TDD-trace gate."
    echo ""
    echo "Edit marks a task status:\"done\" but its commit ($SHA) fails the"
    echo "TDD-trace check: ${problems%; }."
    echo ""
    echo "The task's atomic commit MUST contain its test file AND a \`TDD:\` line"
    echo "in the message body. Re-commit with the test + TDD: trace, then retry."
    echo ""
    echo "See the agentic-loop skill's references/tdd.md."
  } >&2
  exit 2
fi

exit 0
