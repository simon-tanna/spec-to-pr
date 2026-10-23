#!/usr/bin/env bash
# PreToolUse hook — agentic-loop .state transition gate.
# Block transitions into `plan`, `implement`, or `done` without their
# preconditions on disk (Stage 1→2 requires an approved spec-review;
# Stage 2→3 requires an approved plan; Stage 3→4 requires all tasks reviewed).
#
# Triggers on:
#   • Write tool with file_path matching .agentic-loop/<id>/.state
#   • Bash tool with a command that redirects/copies/moves into that path
#
# Why: past CI runs jumped spec→implement directly, skipping the plan
# loop. Without plan.md and tasks.json the per-task TDD cycle has no
# contract to satisfy and review becomes ungrounded. The Bash branch
# closes a bypass that allowed `echo done > .../.state` to set state
# without going through Write.
#
# Pairs with the agentic-loop skill's SKILL.md §Stage Transition Gates.

set -euo pipefail

[ -d .agentic-loop ] || exit 0

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

ID=""
NEW_STATE=""

case "$TOOL_NAME" in
  Write)
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
    [[ "$FILE_PATH" =~ \.agentic-loop/([^/]+)/\.state$ ]] || exit 0
    ID="${BASH_REMATCH[1]}"
    NEW_STATE=$(echo "$INPUT" | jq -r '.tool_input.content // empty' | tr -d '[:space:]')
    ;;

  Bash)
    CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

    # Cheap pre-filter: if no `.agentic-loop/.../.state` anywhere in the
    # command, this hook is irrelevant.
    echo "$CMD" | grep -qE '\.agentic-loop/[^/[:space:]]+/\.state' || exit 0

    TARGET_MATCHES=$(printf '%s\n' "$CMD" | grep -oE \
      '\.agentic-loop/[^/[:space:]]+/\.state' || true)
    TARGET_COUNT=$(printf '%s' "$TARGET_MATCHES" | grep -c . || true)

    if [ "$TARGET_COUNT" -gt 1 ]; then
      {
        echo "Blocked by agentic-loop state-transition gate."
        echo ""
        echo "Bash command references multiple \`.agentic-loop/<id>/.state\`"
        echo "paths. Multi-target writes cannot be statically validated."
        echo "Use the \`Write\` tool — one state transition per call."
      } >&2
      exit 2
    fi

    TARGET=$(printf '%s' "$TARGET_MATCHES" | head -1)
    [ -n "$TARGET" ] || exit 0
    [[ "$TARGET" =~ \.agentic-loop/([^/]+)/\.state$ ]] || exit 0
    ID="${BASH_REMATCH[1]}"

    # Try to extract the literal payload from `echo … > path` /
    # `echo … >> path` / `printf … > path`. Multi-line commands are
    # scanned line-by-line so a heredoc earlier in the script doesn't
    # break the match.
    EXTRACTED_MATCHES=$(printf '%s\n' "$CMD" | grep -oE \
      '(echo|printf)[[:space:]]+([^>]+)>{1,2}[[:space:]]*\.agentic-loop/[^/[:space:]]+/\.state' \
      || true)
    EXTRACTED_COUNT=$(printf '%s' "$EXTRACTED_MATCHES" | grep -c . || true)

    if [ "$EXTRACTED_COUNT" -gt 1 ]; then
      {
        echo "Blocked by agentic-loop state-transition gate."
        echo ""
        echo "Bash command contains multiple writes to \`$TARGET\`. Only one"
        echo "state transition per command is allowed. Use the \`Write\` tool."
      } >&2
      exit 2
    fi

    EXTRACTED=$(printf '%s' "$EXTRACTED_MATCHES" | head -1)

    if [ -n "$EXTRACTED" ]; then
      RAW=$(printf '%s' "$EXTRACTED" \
        | sed -E 's/^(echo|printf)[[:space:]]+//' \
        | sed -E 's/[[:space:]]*>{1,2}[[:space:]]*\.agentic-loop\/[^/[:space:]]+\/\.state$//' \
        | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')
      case "$RAW" in
        \"*\") RAW="${RAW#\"}"; RAW="${RAW%\"}" ;;
        \'*\') RAW="${RAW#\'}"; RAW="${RAW%\'}" ;;
      esac
      # printf with format directives (%s, %d, etc.) is not safe to
      # interpret statically; treat as unparseable.
      if [[ "$EXTRACTED" =~ ^printf[[:space:]] && "$RAW" =~ % ]]; then
        RAW=""
      fi
      NEW_STATE=$(printf '%s' "$RAW" | tr -d '[:space:]')
    fi

    if [ -z "$NEW_STATE" ]; then
      # The path appears in the command but no parseable echo/printf
      # redirect was found. Only block if the command actually points a
      # WRITE at the path (>, >>, tee, cp, mv); read-only references
      # (cat, diff, `[ -f ]`, `git add`, etc.) pass through.
      if ! echo "$CMD" | grep -qE \
        '(>{1,2}[[:space:]]*\.agentic-loop/[^/[:space:]]+/\.state|\btee([[:space:]]+-[a-zA-Z]+)*[[:space:]]+\.agentic-loop/[^/[:space:]]+/\.state|\b(cp|mv)[[:space:]]+[^|;&]*\.agentic-loop/[^/[:space:]]+/\.state)'; then
        exit 0
      fi
      {
        echo "Blocked by agentic-loop state-transition gate."
        echo ""
        echo "A Bash command writes to \`$TARGET\` but the intended state"
        echo "value could not be statically parsed. Allowed forms:"
        echo "  • Write tool with content=<state>"
        echo "  • echo <state> > $TARGET"
        echo ""
        echo "Disallowed: heredocs, tee, cp/mv, multi-redirect chains, printf"
        echo "with format directives. Use \`Write\` so the gate can verify the"
        echo "value before commit."
      } >&2
      exit 2
    fi
    ;;

  *)
    exit 0
    ;;
esac

DIR=".agentic-loop/$ID"

# Policies are shipped alongside wrappers for standalone hook installations.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib-gates.sh"
gate_state "$DIR" "$NEW_STATE"
