#!/usr/bin/env bash
# Harness-agnostic human notification. ALL "tell a human" I/O routes through here:
# loop banners, open questions, progress updates, blocked/permission escalations,
# and PR announcements. This is what lets the loop run AFK outside GitHub Actions
# (a Cloudflare Sandbox/Container, a self-hosted runner, ...) instead of hard-
# failing on the `gh` CLI.
#
# Usage: notify.sh <kind> <id> <body-file-or-dash>
#   kind ∈ banner | questions | progress | blocked | pr
#   id   = issue number OR harness-neutral task id ($AGENTIC_TASK_ID)
#   body = a file path, or "-" to read the body from stdin
#
# Adapter resolution (mirrors SKILL.md §Operating Modes, Axis B):
#   $AGENTIC_IO_ADAPTER → config .io.adapter → github (gh authed / $GITHUB_ACTIONS) → file
#
# GitHub notifications use the real issue from run metadata, falling back to
# the file backend for issue-less runs. This does not change PR adapter selection.
# Legacy numeric IDs without metadata still delegate to gh-comment.sh.

set -euo pipefail

KIND="${1:?kind required (banner|questions|progress|blocked|pr)}"
ID="${2:?id required (issue number or task id)}"
SRC="${3:?body file or '-' required}"

if [ "$SRC" = "-" ]; then
  BODY="$(cat)"
else
  [ -f "$SRC" ] || { echo "notify: body file not found: $SRC" >&2; exit 1; }
  BODY="$(cat "$SRC")"
fi

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

ADAPTER="${AGENTIC_IO_ADAPTER:-$(jq -r '.io.adapter // empty' .agentic-loop.config.json 2>/dev/null || true)}"
if [ -z "$ADAPTER" ]; then
  { [ "${GITHUB_ACTIONS:-}" = "true" ] || gh auth status >/dev/null 2>&1; } \
    && ADAPTER=github || ADAPTER=file
fi

ISSUE="$ID"
if [ "$ADAPTER" = github ]; then
  METADATA="$ROOT/.agentic-loop/$ID/run-context.json"
  if [ -e "$METADATA" ]; then
    ISSUE=$(jq -er '
      if type != "object" then error("expected run metadata object")
      elif (has("issue") | not) then error("missing issue field")
      elif .issue == null then ""
      elif ((.issue | type) == "string" or (.issue | type) == "number")
        and (.issue | tostring | test("^[1-9][0-9]*$")) then .issue | tostring
      else error("issue must be a positive integer or null") end
    ' "$METADATA") || { echo 'notify: invalid run issue metadata' >&2; exit 1; }
  elif [[ ! "$ID" =~ ^[1-9][0-9]*$ ]]; then
    ISSUE=''
  fi
  [ -n "$ISSUE" ] || ADAPTER=file
fi

case "$ADAPTER" in
  github)
    bash "$DIR/gh-comment.sh" "$ISSUE" - <<<"$BODY"
    ;;
  file)
    LOG="$ROOT/.agentic-loop/${ID}/notifications.md"
    mkdir -p "$(dirname "$LOG")"
    { printf '\n---\n## [%s] %s\n\n' "$KIND" "$(date -u +%FT%TZ)"; printf '%s\n' "$BODY"; } >> "$LOG"
    # Also stream a machine-readable marker so a watching harness can react live.
    printf '::agentic-notify kind=%s id=%s::\n%s\n' "$KIND" "$ID" "$BODY"
    ;;
  webhook)
    URL="${AGENTIC_NOTIFY_WEBHOOK:-$(jq -r '.io.webhook_url // empty' .agentic-loop.config.json 2>/dev/null || true)}"
    [ -n "$URL" ] || { echo "notify: webhook adapter but no url (AGENTIC_NOTIFY_WEBHOOK / .io.webhook_url)" >&2; exit 1; }
    jq -nc --arg k "$KIND" --arg id "$ID" --arg b "$BODY" '{kind:$k, id:$id, body:$b}' \
      | curl -fsS -X POST -H 'content-type: application/json' --data @- "$URL" >/dev/null
    ;;
  command)
    CMD="${AGENTIC_NOTIFY_COMMAND:-$(jq -r '.io.notify_command // empty' .agentic-loop.config.json 2>/dev/null || true)}"
    [ -n "$CMD" ] || { echo "notify: command adapter but no notify_command (AGENTIC_NOTIFY_COMMAND / .io.notify_command)" >&2; exit 1; }
    printf '%s' "$BODY" | "$CMD" "$KIND" "$ID"
    ;;
  *)
    echo "notify: unknown IO_ADAPTER '$ADAPTER'" >&2
    exit 1
    ;;
esac
