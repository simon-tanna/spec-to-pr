#!/usr/bin/env bash
# PreToolUse hook: force first tool call to be Skill(skill='agentic-loop')
# when running in CI on a pinned agentic-loop branch.
#
# No-op when:
#   - $AGENTIC_BRANCH unset (interactive use, or non-issue CI events)
#   - .agentic-loop/<issue>/.state already exists (skill already ran once)
#
# Block exit 2 when:
#   - Pin step ran (AGENTIC_BRANCH set) AND state file missing
#   - AND the proposed tool call is anything other than Skill(skill='agentic-loop')

set -euo pipefail

[ -z "${AGENTIC_BRANCH:-}" ] && exit 0
[ -z "${AGENTIC_ISSUE:-}" ] && exit 0

SENTINEL="/tmp/agentic-loop-launched-${AGENTIC_ISSUE}"
STATE_FILE=".agentic-loop/${AGENTIC_ISSUE}/.state"

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
Blocked: agentic-loop skill must be your first tool call in this CI run.

Pinned branch: $AGENTIC_BRANCH
Issue: #$AGENTIC_ISSUE

Invoke the skill now:
  Skill(skill='spec-to-pr:agentic-loop')

After the skill is launched, this hook becomes a no-op for the rest of the run.
MSG
exit 2
