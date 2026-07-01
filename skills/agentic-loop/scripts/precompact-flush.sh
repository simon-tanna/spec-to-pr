#!/usr/bin/env bash
# PreCompact hook: flush agentic-loop state to git before any compaction.
# Enforces the "state in git before reset" invariant regardless of whether the
# context-hygiene heuristic has already triggered.
#
# Input: JSON on stdin (hook event). Output: always exits 0.

set -euo pipefail

[ "${GITHUB_ACTIONS:-}" = "true" ] || exit 0

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
GIT_SYNC="$REPO_ROOT/.claude/skills/agentic-loop/scripts/git-sync.sh"

[ -f "$GIT_SYNC" ] || exit 0

bash "$GIT_SYNC" checkpoint "chore(loop): pre-compact state flush" 2>/dev/null || true

exit 0
