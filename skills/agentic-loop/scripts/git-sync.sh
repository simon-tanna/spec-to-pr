#!/usr/bin/env bash
# Single source of truth for state-file persistence in the agentic-loop.
#
# The skill mutates files under .agentic-loop/<id>/ throughout every stage.
# Those mutations only survive across CI runs / context windows if they are
# committed AND pushed to the deterministic feature branch (which the
# workflow's "Pin agentic-loop branch" step pins HEAD to before the action
# starts). This script is the only place that does that pairing — everything
# else in the skill calls in here.
#
# Usage:
#   git-sync.sh commit "<message>"      # stage .agentic-loop/, commit, push
#   git-sync.sh checkpoint "<reason>"   # same as commit, but tolerates empty diff

set -euo pipefail

ACTION="${1:?action required: commit|checkpoint}"
MESSAGE="${2:?message required}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

log() { printf '\n\033[1;34m[git-sync]\033[0m %s\n' "$*"; }
fail() { printf '\n\033[1;31m[git-sync FAIL]\033[0m %s\n' "$*" >&2; exit 1; }

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[ "$BRANCH" = "HEAD" ] && fail "detached HEAD; refusing to push"
[ "$BRANCH" = "main" ] && fail "refusing to commit on main"

# Stage state-files plus anything the caller already staged.
# Exclude runtime control files — counter is per-session and eject-flag/reason
# are consumed in-process; none should survive a CI checkout.
git add -A .agentic-loop/ \
  ':(exclude).agentic-loop/turn-counter' \
  ':(exclude).agentic-loop/eject-flag' \
  ':(exclude).agentic-loop/eject-reason' \
  2>/dev/null || true

# Empty-diff handling.
if git diff --cached --quiet; then
  case "$ACTION" in
    checkpoint)
      log "no staged changes; checkpoint is a no-op on $BRANCH"
      exit 0
      ;;
    commit)
      fail "commit requested but nothing staged"
      ;;
    *)
      fail "unknown action: $ACTION"
      ;;
  esac
fi

case "$ACTION" in
  commit|checkpoint) ;;
  *) fail "unknown action: $ACTION" ;;
esac

log "commit on $BRANCH: $MESSAGE"
git commit -m "$MESSAGE"

log "push origin $BRANCH"
if ! git push origin "$BRANCH"; then
  log "push rejected; fetch + rebase + retry once"
  git fetch origin "$BRANCH" || fail "fetch failed"
  git rebase "origin/$BRANCH" || fail "rebase conflict — manual intervention required"
  git push origin "$BRANCH" || fail "push failed after rebase"
fi

log "synced $(git rev-parse --short HEAD) to origin/$BRANCH"
