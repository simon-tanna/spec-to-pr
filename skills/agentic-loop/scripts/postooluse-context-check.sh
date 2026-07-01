#!/usr/bin/env bash
# PostToolUse hook: heuristic context check every 15 tool calls.
# Drops .agentic-loop/eject-flag when estimated token usage exceeds the model
# threshold. The agentic-loop skill polls this flag at per-task checkpoints and
# exits cleanly so the next CI trigger resumes from committed state.
#
# Input: JSON on stdin (hook event). Output: always exits 0 — never blocks tools.

set -euo pipefail

# Only active in GitHub Actions
[ "${GITHUB_ACTIONS:-}" = "true" ] || exit 0

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
STATE_DIR="$REPO_ROOT/.agentic-loop"
COUNTER_FILE="$STATE_DIR/turn-counter"
EJECT_FLAG="$STATE_DIR/eject-flag"
EJECT_REASON="$STATE_DIR/eject-reason"

INPUT=$(cat)

TRANSCRIPT_PATH=$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null || true)
[ -n "$TRANSCRIPT_PATH" ] || exit 0
[ -f "$TRANSCRIPT_PATH" ]  || exit 0

mkdir -p "$STATE_DIR"

# Increment counter
COUNTER=0
[ -f "$COUNTER_FILE" ] && COUNTER=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
COUNTER=$((COUNTER + 1))
printf '%d' "$COUNTER" > "$COUNTER_FILE"

# Check every 15 tool calls
[ $((COUNTER % 15)) -eq 0 ] || exit 0

# Already flagged — skip re-estimation
[ -f "$EJECT_FLAG" ] && exit 0

# Token estimate: transcript byte count ÷ 4 (heuristic, ±15%)
TRANSCRIPT_BYTES=$(wc -c < "$TRANSCRIPT_PATH" 2>/dev/null || echo 0)
EST_TOKENS=$(( TRANSCRIPT_BYTES / 4 ))

# Model-specific threshold. CLAUDE_MODEL is stamped by the workflow env.
# The [1m] suffix (or `1m` substring) signals the 1M-context variant of Opus 4.7,
# which has ~10x the window of the standard variant. Detect it explicitly and
# raise the threshold to 600k (60% utilisation — generous headroom for the
# remaining transcript after the eject decision lands).
MODEL="${CLAUDE_MODEL:-claude-opus-4-7}"
if printf '%s' "$MODEL" | grep -qiE '(\[1m\]|[-_]1m($|[^a-z0-9]))'; then
  THRESHOLD=600000  # opus 4.7 [1m] — 1M context, eject at 60%
elif printf '%s' "$MODEL" | grep -qi 'sonnet'; then
  THRESHOLD=160000  # sonnet 4.x — ~200k window, eject at 80%
else
  THRESHOLD=400000  # opus default — ~500k window, eject at 80%
fi

if [ "$EST_TOKENS" -gt "$THRESHOLD" ]; then
  printf 'est %d tokens > threshold %d (model: %s, counter: %d)' \
    "$EST_TOKENS" "$THRESHOLD" "$MODEL" "$COUNTER" > "$EJECT_REASON"
  touch "$EJECT_FLAG"
  exit 0
fi

# Wall-clock budget: GH_TOKEN is a GitHub App installation token capped
# at 60 min. Eject at 45 min so the eject commit + auto-resume issue
# comment can land before the token expires (15-min cushion). Reuses the
# same eject-flag/eject-reason files as the token check so the skill's
# resume-attempts counter (cap 10) gates this path too.
if [[ "${AGENTIC_RUN_STARTED_AT:-}" =~ ^[0-9]+$ ]]; then
  NOW=$(date +%s)
  ELAPSED=$(( NOW - AGENTIC_RUN_STARTED_AT ))
  if [ "$ELAPSED" -gt 2700 ]; then
    printf 'wall-clock %d s > 2700 s budget (GH_TOKEN cliff at 3600 s; counter: %d)' \
      "$ELAPSED" "$COUNTER" > "$EJECT_REASON"
    touch "$EJECT_FLAG"
  fi
fi

exit 0
