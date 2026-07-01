#!/usr/bin/env bash
# PreToolUse hook — enforces a strict TypeScript baseline (no `any`, no type/lint
# suppressions) on Write/Edit of TS files. The rules are built in below; if the repo
# defines its own `.claude/rules/typescript.md`, treat that as the canonical spec.
# Exit 2 + stderr message = block the tool call.
#
# This hook is opt-in and TypeScript-specific — only register it in TS projects.

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')

[[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" ]] || exit 0

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only inspect TS source files
[[ "$FILE_PATH" =~ \.(ts|tsx|mts|cts)$ ]] || exit 0
[[ "$FILE_PATH" =~ \.d\.ts$ ]] && exit 0

if [[ "$TOOL_NAME" == "Write" ]]; then
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
else
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')
fi

[[ -z "$CONTENT" ]] && exit 0

VIOLATIONS=()

# Strip single-line comments, block comments, and string literals to avoid
# false positives (e.g. "company" matching "any", docs mentioning "any")
STRIPPED=$(echo "$CONTENT" \
  | sed 's|//[^\n]*||g' \
  | sed 's|/\*.*\*/||g' \
  | sed "s|'[^']*'|''|g" \
  | sed 's|"[^"]*"|""|g' \
  | sed 's|`[^`]*`|``|g')

# any — word-bounded forms only
echo "$STRIPPED" | grep -qE ':\s*any\b'           && VIOLATIONS+=('`: any` type annotation')
echo "$STRIPPED" | grep -qE '\bas\s+any\b'         && VIOLATIONS+=('`as any` assertion')
echo "$STRIPPED" | grep -qE '<\s*any\s*[,>]'       && VIOLATIONS+=('`<any>` generic argument')
echo "$STRIPPED" | grep -qE '\bany\s*\[\s*\]'      && VIOLATIONS+=('`any[]` array type')
echo "$STRIPPED" | grep -qE '\bArray\s*<\s*any\s*>' && VIOLATIONS+=('`Array<any>` type')
echo "$STRIPPED" | grep -qE '\bRecord\s*<[^,>]+,\s*any\s*>' && VIOLATIONS+=('`Record<K, any>` type')
echo "$STRIPPED" | grep -qE '\.\.\.\s*\w+\s*:\s*any\b' && VIOLATIONS+=('`...args: any` rest param')

# TS suppression — check raw content (these only occur in comments)
echo "$CONTENT" | grep -qE '@ts-(ignore|expect-error|nocheck)\b' \
  && VIOLATIONS+=('TypeScript suppression directive (`@ts-ignore` / `@ts-expect-error` / `@ts-nocheck`)')

# ESLint disable — check raw content
echo "$CONTENT" | grep -qE 'eslint-disable(-next-line|-line)?\b' \
  && VIOLATIONS+=('ESLint disable directive')

[[ ${#VIOLATIONS[@]} -eq 0 ]] && exit 0

{
  echo "Blocked by TypeScript rules (see .claude/rules/typescript.md if the repo defines one):"
  echo ""
  for v in "${VIOLATIONS[@]}"; do
    echo "  • $v"
  done
  echo ""
  echo "These rules are non-negotiable and cannot be overridden by skills or subagents."
  echo "Fix the type properly. If truly unavoidable, stop and ask the user for explicit approval."
  echo ""
  echo "Prefer: specific types → generics → unknown+narrowing → discriminated unions."
} >&2

exit 2
