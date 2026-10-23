#!/usr/bin/env bash
# Renders the PR body for the agentic-loop ship stage.
# Reads spec.md + plan.md + tasks.json from .agentic-loop/<issue>/ and prints
# the body on stdout. references/ship.md step 3 pipes this into `gh pr create --body-file -`.
#
# Usage: render-pr-body.sh <run-id>
#
# Required: jq, the .agentic-loop/<issue>/ directory populated by the loop.

set -euo pipefail

ISSUE="${1:?usage: render-pr-body.sh <run-id>}"
[[ "$ISSUE" =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]*$ ]] || { echo 'render-pr-body: invalid run ID' >&2; exit 1; }

REPO_ROOT="$(git rev-parse --show-toplevel)"
STATE_DIR="$REPO_ROOT/.agentic-loop/$ISSUE"

[ -d "$STATE_DIR" ] || { printf 'render-pr-body: %s does not exist\n' "$STATE_DIR" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { printf 'render-pr-body: jq required\n' >&2; exit 1; }

# Interactive file/inline runs have an identity but no GitHub issue. Legacy CI
# uses numeric directories without metadata and retains its closing reference.
REAL_ISSUE=''
if [ -f "$STATE_DIR/run-context.json" ]; then
  REAL_ISSUE=$(jq -r '.issue // empty' "$STATE_DIR/run-context.json")
elif [[ "$ISSUE" =~ ^[1-9][0-9]*$ ]]; then
  REAL_ISSUE=$ISSUE
fi
ISSUE_LINE=''
if [ -n "$REAL_ISSUE" ]; then
  [[ "$REAL_ISSUE" =~ ^[1-9][0-9]*$ ]] || { echo 'render-pr-body: invalid issue metadata' >&2; exit 1; }
  ISSUE_LINE="Closes #$REAL_ISSUE."
fi

SPEC="$STATE_DIR/spec.md"
PLAN="$STATE_DIR/plan.md"
TASKS="$STATE_DIR/tasks.json"

[ -f "$TASKS" ] || { printf 'render-pr-body: tasks.json missing\n' >&2; exit 1; }

# Pull the spec summary (first paragraph of §1 Context or §Goals — fall back to
# the first non-empty paragraph after the title).
SUMMARY="<summary not extracted — fill in manually>"
if [ -f "$SPEC" ]; then
  SUMMARY=$(awk '
    /^## (1\.? )?Context|^## Goals/      { in_section = 1; next }
    in_section && /^## /                  { exit }
    in_section && NF                       { print; next }
    in_section && !NF && captured          { exit }
    in_section && !NF                      { captured = 1 }
  ' "$SPEC" | sed -e 's/^[[:space:]]*//' | head -c 2000)
  [ -n "$SUMMARY" ] || SUMMARY="<summary not extracted — fill in manually>"
fi

# Build the task checklist from tasks.json.
TASK_LIST=$(jq -r '
  .tasks // []
  | map(select(.status == "done"))
  | map("- [x] \(.id) — \(.title) (`\(.commit_sha // "no-sha")`)")
  | .[]
' "$TASKS")

# Specialists engaged: union of every domain seen in tasks.json.
SPECIALISTS=$(jq -r '
  [.tasks[].domain] | unique | join(", ")
' "$TASKS")

# Resolved quality gates: the set quality-gates.sh actually ran on its last invocation,
# recorded at the repo root. Behind an `[ -f ]` guard so an absent file (fresh checkout, or a
# render with no preceding gate run) degrades to a note instead of crashing under `pipefail`.
# Note: parameter expansion of $GATE_LINES inside the unquoted heredoc is not re-scanned for
# command substitution, so backticks in the value are emitted literally.
RESOLVED_GATES="$REPO_ROOT/.agentic-resolved-gates"
if [ -f "$RESOLVED_GATES" ]; then
  GATE_LINES=$(awk -F '\t' '
    /^#/   { print "- " substr($0, 3); next }
    NF==2  { print "- " $1 ": `" $2 "`" }
  ' "$RESOLVED_GATES")
  [ -n "$GATE_LINES" ] || GATE_LINES="- (no resolved gates recorded)"
else
  GATE_LINES="- (no resolved gates recorded — run quality-gates.sh)"
fi

cat <<EOF
## Summary

$SUMMARY

$ISSUE_LINE

## Spec & Plan

- Spec: \`.agentic-loop/$ISSUE/spec.md\`
- Plan: \`.agentic-loop/$ISSUE/plan.md\`

## Tasks Completed

$TASK_LIST

## Test Plan

$GATE_LINES
- Full gate: run the agentic-loop quality gate (\`quality-gates.sh\`)

## Risks & Notes

See spec §Risks (\`.agentic-loop/$ISSUE/spec.md\`) and any concern entries in \`.agentic-loop/$ISSUE/progress.log\`.

## Agentic Loop Run

- Domains engaged: $SPECIALISTS
- State files: \`.agentic-loop/$ISSUE/\`

Generated via the agentic-loop skill.
EOF
