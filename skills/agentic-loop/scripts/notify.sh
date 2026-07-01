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
# Output: exit 0 on success. The github branch preserves today's behaviour
# exactly (delegates to gh-comment.sh, keeping the @author tag).

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

ADAPTER="${AGENTIC_IO_ADAPTER:-$(jq -r '.io.adapter // empty' .agentic-loop.config.json 2>/dev/null || true)}"
if [ -z "$ADAPTER" ]; then
  { [ "${GITHUB_ACTIONS:-}" = "true" ] || gh auth status >/dev/null 2>&1; } \
    && ADAPTER=github || ADAPTER=file
fi

case "$ADAPTER" in
  github)
    # Unchanged behaviour: delegate to gh-comment.sh (keeps @author tagging).
    bash "$DIR/gh-comment.sh" "$ID" - <<<"$BODY"
    ;;
  file)
    ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
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
