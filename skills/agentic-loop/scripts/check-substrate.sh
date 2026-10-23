#!/usr/bin/env bash
# Report controller checks separately from Claude lifecycle registration.
# No arguments retains the Claude probe and its 0=installed/1=incomplete contract.
set -euo pipefail
HARNESS=claude
if [ "$#" -gt 0 ]; then
  if [ "$#" -ne 2 ] || [ "$1" != --harness ]; then
    echo 'usage: check-substrate.sh [--harness claude|codex]' >&2; exit 1
  fi
  HARNESS=$2
fi
case "$HARNESS" in claude|codex) ;; *) echo 'unknown harness' >&2; exit 1 ;; esac
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
log() { printf '[check-substrate] %s\n' "$*"; }
warn() { printf '[check-substrate WARN] %s\n' "$*" >&2; }
if [ ! -r "$SCRIPT_DIR/../setup/hooks/lib-gates.sh" ] || [ ! -r "$SCRIPT_DIR/check-gates.sh" ] || ! command -v jq >/dev/null; then
  warn 'controller-invoked checks unavailable: check installation and jq'; exit 1
fi
log 'controller-invoked checks available (explicit calls required)'
if [ "$HARNESS" = codex ]; then
  log 'Codex: no lifecycle interception; Claude settings do not apply'
  exit 0
fi
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || { warn 'not in a Git repository'; exit 1; }
SETTINGS="$REPO_ROOT/.claude/settings.json"
[ -f "$SETTINGS" ] || { warn 'Claude gate hooks NOT registered; controller-invoked checks only'; exit 1; }
GATE_HOOKS=(agentic-loop-check-state-transition.sh agentic-loop-check-tasks-json.sh agentic-loop-check-pr-ready.sh agentic-loop-check-tdd-trace.sh)
missing=0
for h in "${GATE_HOOKS[@]}"; do
  if jq -e --arg suffix "/.claude/hooks/$h" '[.hooks.PreToolUse[]?.hooks[]? | select(.type == "command") | .command | select(endswith($suffix) or endswith($suffix + "\""))] | length > 0' "$SETTINGS" >/dev/null 2>&1; then
    log "registered: $h"
  else
    warn "NOT registered: $h"; missing=1
  fi
  if [ ! -x "$REPO_ROOT/.claude/hooks/$h" ]; then
    warn "installed executable missing: $h"; missing=1
  fi
done
if [ ! -r "$REPO_ROOT/.claude/hooks/lib-gates.sh" ]; then
  warn 'installed shared helper missing: lib-gates.sh'; missing=1
fi
[ "$missing" -eq 0 ] || { warn 'Claude lifecycle setup incomplete; controller-invoked checks available'; exit 1; }
log 'all four Claude gate hooks registered and local dependencies present'
log 'registration probe only; verify interception in the active Claude session'
