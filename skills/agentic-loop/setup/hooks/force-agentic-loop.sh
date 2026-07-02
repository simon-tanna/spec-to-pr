#!/usr/bin/env bash
# PreToolUse hook: force first tool call to be Skill(skill='agentic-loop')
# when running headless on a pinned agentic-loop task.
#
# Fires when the GitHub pin step ran ($AGENTIC_BRANCH set) OR a non-GitHub
# headless harness opts in with $AGENTIC_FORCE=1. Needs a task id for the
# sentinel/state path: $AGENTIC_TASK_ID (falls back to $AGENTIC_ISSUE).
#
# No-op when:
#   - neither $AGENTIC_BRANCH nor $AGENTIC_FORCE=1 is set (interactive use, non-issue events)
#   - no task id resolvable
#   - .agentic-loop/<id>/.state already exists (skill already ran once)
#
# Block exit 2 when:
#   - gate active AND state file missing
#   - AND the proposed tool call is anything other than Skill(skill='agentic-loop')

set -euo pipefail

: "${AGENTIC_TASK_ID:=${AGENTIC_ISSUE:-}}"
{ [ -n "${AGENTIC_BRANCH:-}" ] || [ "${AGENTIC_FORCE:-}" = "1" ]; } || exit 0
[ -z "$AGENTIC_TASK_ID" ] && exit 0

SENTINEL="/tmp/agentic-loop-launched-${AGENTIC_TASK_ID}"
STATE_FILE=".agentic-loop/${AGENTIC_TASK_ID}/.state"

# Skill already launched once OR state file persisted; hook is a no-op.
[ -f "$SENTINEL" ] && exit 0
[ -f "$STATE_FILE" ] && exit 0

INPUT="$(cat)"
TOOL_NAME="$(printf '%s' "$INPUT" | jq -r '.tool_name // empty')"
SKILL_PARAM="$(printf '%s' "$INPUT" | jq -r '.tool_input.skill // empty')"

# Allow the Skill(agentic-loop) launch and mark the sentinel so subsequent
# tool calls (the skill's own Bash/Write/etc.) pass freely. Accept both the
# plugin-qualified name (spec-to-pr:agentic-loop) and the bare name.
if [ "$TOOL_NAME" = "Skill" ] && { [ "$SKILL_PARAM" = "spec-to-pr:agentic-loop" ] || [ "$SKILL_PARAM" = "agentic-loop" ]; }; then
  touch "$SENTINEL"
  exit 0
fi

cat >&2 <<MSG
Blocked: agentic-loop skill must be your first tool call in this headless run.

Pinned branch: ${AGENTIC_BRANCH:-<none>}
Task: ${AGENTIC_TASK_ID}

Invoke the skill now:
  Skill(skill='spec-to-pr:agentic-loop')

After the skill is launched, this hook becomes a no-op for the rest of the run.
MSG
exit 2
