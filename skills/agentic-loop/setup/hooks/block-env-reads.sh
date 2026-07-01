#!/usr/bin/env bash
# PreToolUse hook — block any tool call that touches .env / secrets / credentials.
# Reads JSON from stdin, exits 2 on match (blocks action, stderr shown to model).

set -euo pipefail

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name')

SENSITIVE_REGEX='(^|[^A-Za-z0-9_.-])\.env(\.[A-Za-z0-9_-]+)?([^A-Za-z0-9_.-]|$)|/secrets/|credentials\.(json|yaml|yml|env)|\.pem([^A-Za-z0-9]|$)|id_rsa|id_ed25519|\.ssh/'
ALLOWLIST_REGEX='\.env\.(example|sample|template|dist)([^A-Za-z0-9]|$)'

check() {
  local haystack="$1"
  if echo "$haystack" | grep -Eq "$ALLOWLIST_REGEX"; then
    haystack=$(echo "$haystack" | sed -E "s/\.env\.(example|sample|template|dist)//g")
  fi
  if echo "$haystack" | grep -Eq "$SENSITIVE_REGEX"; then
    echo "Blocked: tool call references sensitive file (.env / secrets / credentials / key material). Policy: bulletproof-env-block." >&2
    exit 2
  fi
}

case "$TOOL" in
  Bash)
    CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
    check "$CMD"
    ;;
  Read|Edit|Write|NotebookEdit)
    FILE_PATH_ARG=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
    check "$FILE_PATH_ARG"
    ;;
esac

exit 0
