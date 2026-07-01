#!/usr/bin/env bash
# Setup probe for the agentic-loop substrate.
#
# Reports whether the three deterministic gate hooks are REGISTERED in
# .claude/settings.json (merely having the script files present is not enough —
# the hooks only fire when registered). Used by the loop and by a human running
# setup to know whether stage-gate enforcement is deterministic (hooks fire) or
# model-only (controller must self-enforce — see references/stage-gates.md).
#
# Exit 0: all three gate hooks registered. Exit 1: one or more missing. The loop
# treats exit 1 as "enforcement is model-only" — it warns and continues; it does
# NOT block, because the gates still hold via the controller.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SETTINGS="$REPO_ROOT/.claude/settings.json"

GATE_HOOKS=(
  agentic-loop-check-state-transition.sh
  agentic-loop-check-tasks-json.sh
  agentic-loop-check-pr-ready.sh
)

log()  { printf '[check-substrate] %s\n' "$*"; }
warn() { printf '[check-substrate WARN] %s\n' "$*" >&2; }

if [ ! -f "$SETTINGS" ]; then
  warn "no .claude/settings.json — gate hooks are NOT registered."
  warn "Stage-gate enforcement is model-only. To make it deterministic, follow"
  warn "setup/SETUP.md (merge setup/settings.snippet.json into .claude/settings.json)."
  exit 1
fi

missing=0
for h in "${GATE_HOOKS[@]}"; do
  # Registered = the hook filename appears as a command string in settings.json.
  if grep -q "$h" "$SETTINGS" 2>/dev/null; then
    log "registered: $h"
  else
    warn "NOT registered: $h"
    missing=1
  fi
done

if [ "$missing" -eq 1 ]; then
  warn "One or more gate hooks are unregistered — stage-gate enforcement is model-only."
  warn "See setup/SETUP.md to register them."
  exit 1
fi

log "all three gate hooks registered — stage gates are deterministically enforced."
exit 0
