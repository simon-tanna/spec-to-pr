#!/usr/bin/env bash
# PreToolUse hook — block secret exfiltration via Bash.
# Reads JSON from stdin, exits 2 on match.
#
# Blocks:
#   - env-dump: bare `env`, `env |`, `printenv`, `set | grep`, `cat /proc/*/environ`
#   - token echo: `echo $*TOKEN`, `echo $*SECRET`, etc.
#   - network POST/upload: curl -d/-F/-T, wget --post-*, nc/ncat/socat
#   - python socket / urllib POST (best-effort)
#
# Read-only `curl <URL>` and `wget <URL>` for doc lookups remain allowed.
# `env VAR=val cmd ...` invocation form (env-as-prefix) is allowed.

set -euo pipefail

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name')

[ "$TOOL" = "Bash" ] || exit 0

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

block() {
  echo "Blocked: secret exfil pattern. Policy: block-secret-exfil." >&2
  echo "Reason: $1" >&2
  echo "Command: $CMD" >&2
  echo "Allowed alternatives: 'gh-comment.sh' for status updates, 'WebFetch' for doc lookups, plain 'curl <URL>' GET." >&2
  exit 2
}

NORM=$(printf '%s' "$CMD" | tr '\n' ' ' | tr -s '[:space:]' ' ')
PADDED=" $NORM "

# bare `env` (no args, or piped/redirected) — allow `env VAR=val cmd`
# Match `env` followed by end / pipe / redirect / `&&` / `;` (no VAR=val).
if echo "$PADDED" | grep -Eq '(^|[^A-Za-z0-9_/-])env([[:space:]]*$|[[:space:]]*[|;&><])'; then
  block "bare 'env' (env-dump)"
fi

# printenv (any form dumps env vars by name or all)
if echo "$PADDED" | grep -Eq '(^|[^A-Za-z0-9_/-])printenv([[:space:]]|$)'; then
  block "printenv"
fi

# `set | ...` (set with pipe dumps shell vars including exported env)
if echo "$PADDED" | grep -Eq '(^|[^A-Za-z0-9_/-])set[[:space:]]*\|'; then
  block "'set | ...' (shell var dump)"
fi

# /proc/*/environ
if echo "$PADDED" | grep -Eq '/proc/[^[:space:]/]+/environ'; then
  block "/proc/*/environ read"
fi

# echo $TOKEN-ish
if echo "$PADDED" | grep -Eq '(^|[^A-Za-z0-9_-])(echo|printf)[[:space:]]+[^|;&]*\$\{?[A-Za-z_]*[A-Za-z_-]*(TOKEN|SECRET|PASSWORD|PASSWD|OAUTH|API_KEY|APIKEY|PRIVATE_KEY|CREDENTIAL)[A-Za-z_]*'; then
  block "echo of token/secret/password env var"
fi

# curl POST/upload variants
if echo "$PADDED" | grep -Eq '(^|[^A-Za-z0-9_/-])curl([[:space:]]+[^|;&]*)?[[:space:]](-d([[:space:]]|=)|--data([[:space:]]|=|-)|-F([[:space:]]|=)|--form([[:space:]]|=)|-T([[:space:]]|=)|--upload-file([[:space:]]|=)|--data-binary|--data-raw|--data-urlencode)'; then
  block "curl with POST/upload data flag"
fi

# wget POST/upload
if echo "$PADDED" | grep -Eq '(^|[^A-Za-z0-9_/-])wget([[:space:]]+[^|;&]*)?[[:space:]]--(post-data|post-file|body-data|body-file|method=POST|method=PUT)'; then
  block "wget with POST/PUT body flag"
fi

# nc / ncat / socat — assume exfil channel
if echo "$PADDED" | grep -Eq '(^|[^A-Za-z0-9_/-])(nc|ncat|socat)([[:space:]]|$)'; then
  block "netcat / socat (raw network channel)"
fi

# python -c with socket or urllib POST
if echo "$PADDED" | grep -Eq '(^|[^A-Za-z0-9_/-])python[0-9.]*[[:space:]]+-c[[:space:]][^|;&]*(import[[:space:]]+socket|urllib\.request\.urlopen|requests\.(post|put|patch))'; then
  block "python -c with socket / urllib POST / requests.post"
fi

exit 0
