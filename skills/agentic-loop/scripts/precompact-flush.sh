#!/usr/bin/env bash
# PreCompact hook: flush agentic-loop state to git before any compaction.
# Enforces the "state in git before reset" invariant regardless of whether the
# context-hygiene heuristic has already triggered.
#
# Input: JSON on stdin (hook event). Output: always exits 0.

set -euo pipefail

# Active in ANY headless harness (see lib-mode.sh). Fall back to the legacy
# GITHUB_ACTIONS check if lib-mode.sh was not copied alongside this hook.
_MODE_LIB="$(cd "$(dirname "$0")" && pwd)/lib-mode.sh"
if [ -f "$_MODE_LIB" ]; then
  [ "$(bash "$_MODE_LIB")" = "headless" ] || exit 0
else
  [ "${GITHUB_ACTIONS:-}" = "true" ] || exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0

# Locate git-sync.sh across install layouts: alongside this script (plugin
# scripts dir), copied into the repo's .claude/hooks/, or the legacy in-repo
# skill layout. No-op safely if none is found.
GIT_SYNC=""
for cand in \
  "$(cd "$(dirname "$0")" && pwd)/git-sync.sh" \
  "$REPO_ROOT/.claude/hooks/git-sync.sh" \
  "$REPO_ROOT/.claude/skills/agentic-loop/scripts/git-sync.sh"; do
  [ -f "$cand" ] && { GIT_SYNC="$cand"; break; }
done
[ -n "$GIT_SYNC" ] || exit 0

bash "$GIT_SYNC" checkpoint "chore(loop): pre-compact state flush" 2>/dev/null || true

exit 0
