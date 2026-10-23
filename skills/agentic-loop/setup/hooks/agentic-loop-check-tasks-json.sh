#!/usr/bin/env bash
# PreToolUse hook — agentic-loop tasks.json gate.
# Block Write/Edit on .agentic-loop/<id>/tasks.json that marks any task
# status:"done" without populated spec_review_sha AND quality_review_sha.
#
# Why: the loop's quality story rests on per-task two-stage review (spec-
# compliance + code-quality). The model has skipped this in past CI runs
# to conserve turns. Hook makes the skip impossible.
#
# Pairs with the agentic-loop skill's references/execution-loop.md.

set -euo pipefail

# Project-scope guard: inert outside loop runs.
[ -d .agentic-loop ] || exit 0

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

[[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" ]] || exit 0

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only inspect tasks.json under .agentic-loop/<id>/
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
gate_tasks "$MODE" "$PROPOSED"
