#!/usr/bin/env bash
# PreToolUse hook — block destructive git/gh operations from Bash.
# Reads JSON from stdin, exits 2 on match (blocks tool call, stderr shown to model).
#
# Blocks:
#   - force-push variants (--force, -f, --force-with-lease, --mirror)
#   - branch deletion (git branch -D / -d, git push --delete, git push :refspec)
#   - history rewrite (git reset --hard, git filter-branch, git filter-repo)
#   - GH API ref deletion (gh api ... -X DELETE on refs/heads or git/refs)

set -euo pipefail

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name')

[ "$TOOL" = "Bash" ] || exit 0

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

block() {
  echo "Blocked: destructive git/gh operation. Policy: block-destructive-git." >&2
  echo "Reason: $1" >&2
  echo "Command: $CMD" >&2
  echo "Allowed: regular 'git push', 'git rebase origin/<branch>', 'git fetch', non-destructive 'gh' calls." >&2
  exit 2
}

# Normalise to single-spaced for matching.
NORM=$(printf '%s' "$CMD" | tr '\n' ' ' | tr -s '[:space:]' ' ')

# git push --force / -f / --force-with-lease / --mirror
if echo " $NORM " | grep -Eq '(^|[^A-Za-z0-9_-])git[[:space:]]+push([[:space:]]+[^|;&]*)?[[:space:]](--force([= ]|$)|--force-with-lease([= ]|$)|-f[[:space:]]|-f$|--mirror([ =]|$))'; then
  block "git push with --force / -f / --force-with-lease / --mirror"
fi

# git push --delete
if echo " $NORM " | grep -Eq '(^|[^A-Za-z0-9_-])git[[:space:]]+push[[:space:]][^|;&]*--delete([ =]|$)'; then
  block "git push --delete"
fi

# git push origin :refspec (delete syntax) — refspec arg starting with ':'
if echo " $NORM " | grep -Eq '(^|[^A-Za-z0-9_-])git[[:space:]]+push[[:space:]][^|;&]*[[:space:]]:[A-Za-z0-9_./-]+'; then
  block "git push :<refspec> (branch-delete syntax)"
fi

# git branch -D / -d / --delete
if echo " $NORM " | grep -Eq '(^|[^A-Za-z0-9_-])git[[:space:]]+branch([[:space:]]+[^|;&]*)?[[:space:]]+-(D|d|-delete)([[:space:]]|=|$)'; then
  block "git branch -d / -D / --delete (branch deletion)"
fi

# git reset --hard
if echo " $NORM " | grep -Eq '(^|[^A-Za-z0-9_-])git[[:space:]]+reset[[:space:]][^|;&]*--hard([[:space:]]|$)'; then
  block "git reset --hard (history rewrite)"
fi

# git filter-branch / filter-repo
if echo " $NORM " | grep -Eq '(^|[^A-Za-z0-9_-])git[[:space:]]+filter-(branch|repo)([[:space:]]|$)'; then
  block "git filter-branch / filter-repo (history rewrite)"
fi

# gh api ... DELETE on refs
if echo " $NORM " | grep -Eq '(^|[^A-Za-z0-9_-])gh[[:space:]]+api[[:space:]][^|;&]*(-X[[:space:]]+DELETE|--method[[:space:]]+DELETE|--method=DELETE)[^|;&]*(refs/heads|git/refs)'; then
  block "gh api DELETE on refs/heads or git/refs"
fi
if echo " $NORM " | grep -Eq '(^|[^A-Za-z0-9_-])gh[[:space:]]+api[[:space:]][^|;&]*(refs/heads|git/refs)[^|;&]*(-X[[:space:]]+DELETE|--method[[:space:]]+DELETE|--method=DELETE)'; then
  block "gh api DELETE on refs/heads or git/refs"
fi

# gh repo delete (full repo nuke)
if echo " $NORM " | grep -Eq '(^|[^A-Za-z0-9_-])gh[[:space:]]+repo[[:space:]]+delete([[:space:]]|$)'; then
  block "gh repo delete"
fi

exit 0
