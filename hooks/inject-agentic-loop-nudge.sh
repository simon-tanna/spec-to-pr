#!/usr/bin/env bash
# UserPromptSubmit hook (plugin-level, always active on install).
#
# Local parallel to the CI-only setup/hooks/force-agentic-loop.sh. In a local
# interactive session the agentic-loop skill under-triggers: it relies solely on
# its frontmatter description and loses to plan mode and superpowers:brainstorming.
# This hook detects spec-shaped prompts and injects additionalContext nudging the
# model to invoke Skill(spec-to-pr:agentic-loop) FIRST.
#
# NUDGE, never block: a false positive costs one small context string, never a
# blocked prompt. Users who legitimately want plain planning are unaffected.
#
# No-op when:
#   - $GITHUB_ACTIONS == "true"        (CI already forces the skill)
#   - $AGENTIC_LOOP_NO_NUDGE non-empty (explicit user opt-out)
#   - jq is unavailable
#   - a loop is already running in this repo (.agentic-loop/<id>/.state exists)
#   - already nudged once this session (/tmp sentinel keyed by session_id)
#   - the prompt is not spec-shaped
#
# Input:  UserPromptSubmit event JSON on stdin (.prompt, .session_id, .cwd).
# Output: exit 0. Either nothing (no-op) or a JSON object carrying
#         hookSpecificOutput.additionalContext.

set -euo pipefail

# 1. CI already forces the skill via force-agentic-loop.sh — never double up.
[ "${GITHUB_ACTIONS:-}" = "true" ] && exit 0

# 2. Explicit opt-out for users who never want the nudge.
[ -n "${AGENTIC_LOOP_NO_NUDGE:-}" ] && exit 0

command -v jq >/dev/null 2>&1 || exit 0

INPUT="$(cat)"
PROMPT="$(printf '%s' "$INPUT" | jq -r '.prompt // empty')"
SESSION_ID="$(printf '%s' "$INPUT" | jq -r '.session_id // empty')"
[ -n "$PROMPT" ] || exit 0

# 3. If a loop is already underway in this repo, the skill is running — no nudge.
#    .agentic-loop/<id>/.state is the loop's durable phase marker (see SKILL.md).
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if compgen -G "$ROOT/.agentic-loop/*/.state" >/dev/null 2>&1; then
  exit 0
fi

# 4. Nudge at most once per session. The sentinel is only set on a MATCH below,
#    so non-matching prompts never burn it — the first spec-shaped prompt wins.
#    Sanitize session_id to a safe filename subset first: it comes from hook
#    input JSON and is interpolated into a /tmp path, so a value carrying `/` or
#    `..` could otherwise steer `touch` outside /tmp (path traversal).
SAFE_SESSION="$(printf '%s' "${SESSION_ID:-nosession}" | tr -c 'A-Za-z0-9_-' '_')"
SENTINEL="/tmp/agentic-loop-nudged-${SAFE_SESSION}"
[ -f "$SENTINEL" ] && exit 0

# 5. Spec-shaped heuristic (two tiers, deliberately conservative).
LOWER="$(printf '%s' "$PROMPT" | tr '[:upper:]' '[:lower:]')"
match=0

# Tier A — the user (near-)named the loop or a spec->PR handoff. High precision;
# a match alone is enough.
if printf '%s' "$LOWER" | grep -Eq \
  'agentic[ -]?loop|spec[ -]?to[ -]?pr|ralph[ -]?(this|it|loop)|run the (agentic )?loop|from spec to (a )?pr'; then
  match=1
fi

# Tier B — a spec/issue ARTIFACT cue AND an implementation-intent VERB. Requiring
# both cuts false positives on pure questions ("what does this spec say?").
if [ "$match" -eq 0 ]; then
  artifact='spec|task card|task-card|acceptance criteria|github issue|issue #|#[0-9]+|\.md|user stor(y|ies)|requirement'
  verb='implement|autonomous|end[ -]?to[ -]?end|from spec|raise a pr|open a pr|take (this|it) to a pr|ship (this|it)|build (this|it) out'
  if printf '%s' "$LOWER" | grep -Eq "$artifact" \
     && printf '%s' "$LOWER" | grep -Eq "$verb"; then
    match=1
  fi
fi

[ "$match" -eq 1 ] || exit 0

# 6. Matched — mark the sentinel and inject the nudge as additionalContext.
touch "$SENTINEL" 2>/dev/null || true

read -r -d '' MSG <<'EOF' || true
This prompt looks like a spec / issue / task-card handoff for end-to-end
implementation. Strongly prefer invoking Skill(spec-to-pr:agentic-loop) to drive
it through the spec->PR pipeline BEFORE defaulting to plan mode or the
superpowers:brainstorming skill. The agentic-loop skill runs its own spec
interview, TDD planning, two-stage review loops and quality gates, so those are
covered inside it. If the user only wants research, Q&A, or a trivial one-line
edit (see the skill's "When NOT to Use"), skip the skill and proceed normally.
This is guidance, not a hard requirement.
EOF

jq -n --arg ctx "$MSG" '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: $ctx
  }
}'

exit 0
