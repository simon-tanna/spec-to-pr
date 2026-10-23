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

# Policies are shipped alongside wrappers for standalone hook installations.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib-gates.sh"
if [[ "$TOOL_NAME" == "Write" ]]; then
  MODE=document
  PROPOSED=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
else
  MODE=fragment
  PROPOSED=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')
fi
gate_tdd "$MODE" "$PROPOSED"
