#!/usr/bin/env bash
# Smoke tests for the plugin-level UserPromptSubmit nudge hook.
# The hook always exits 0, so cases assert on STDOUT (presence/absence of the
# injected additionalContext JSON) rather than exit code.
#
# Usage: bash hooks/__tests__/test-nudge-hook.sh
# Exit:  0 if all scenarios pass; non-zero with diagnostic otherwise.

set -uo pipefail

HOOK="$(cd "$(dirname "$0")/.." && pwd)/inject-agentic-loop-nudge.sh"
[ -x "$HOOK" ] || { echo "missing or non-executable $HOOK"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq required"; exit 1; }

PASS=0
FAIL=0
FAILED_NAMES=()

# Run from a scratch dir so a real .agentic-loop/ in the repo never interferes,
# and so the loop-already-running case can create its own state file.
SANDBOX=$(mktemp -d)
trap 'cd / >/dev/null; rm -rf "$SANDBOX"; rm -f /tmp/agentic-loop-nudged-test-*' EXIT
cd "$SANDBOX"

mk_payload() { # prompt session_id
  jq -nc --arg p "$1" --arg s "$2" '{prompt:$p, session_id:$s}'
}

# expect ∈ {emit, silent}; runs the hook and checks whether additionalContext appeared.
run_case() { # name expect payload [env-assignment...]
  local name="$1" expect="$2" payload="$3"; shift 3
  local out
  out=$(printf '%s' "$payload" | env "$@" bash "$HOOK" 2>/dev/null || true)
  local got=silent
  if printf '%s' "$out" | grep -q 'additionalContext'; then got=emit; fi
  if [ "$got" = "$expect" ]; then
    printf '  ✓ %s\n' "$name"; PASS=$((PASS + 1))
  else
    printf '  ✗ %s (expected %s, got %s)\n' "$name" "$expect" "$got"
    FAIL=$((FAIL + 1)); FAILED_NAMES+=("$name")
  fi
}

echo "== nudge hook =="

# 1. Tier A match -> emits
run_case "1: Tier A 'spec to PR'" emit "$(mk_payload 'take this from spec to PR' test-1)"

# 2. Tier B match (artifact + verb) -> emits
run_case "2: Tier B issue + end-to-end" emit "$(mk_payload 'implement this GitHub issue end-to-end' test-2)"

# 3. Once-per-session: repeat #1's session -> silent (sentinel set in case 1)
run_case "3: repeat same session -> silent" silent "$(mk_payload 'spec to pr again' test-1)"

# 4. Non-spec prompt -> silent
run_case "4: plain question -> silent" silent "$(mk_payload 'what does this function do?' test-4)"

# 5. Tier B partial (artifact, no verb) -> silent
run_case "5: artifact only, no verb -> silent" silent "$(mk_payload 'summarise the requirements doc' test-5)"

# 6. CI no-op -> silent
run_case "6: GITHUB_ACTIONS=true -> silent" silent "$(mk_payload 'implement this issue end to end' test-6)" GITHUB_ACTIONS=true

# 7. Opt-out -> silent
run_case "7: AGENTIC_LOOP_NO_NUDGE -> silent" silent "$(mk_payload 'ralph this' test-7)" AGENTIC_LOOP_NO_NUDGE=1

# 8. Loop already running (state file present) -> silent
mkdir -p .agentic-loop/42 && : > .agentic-loop/42/.state
run_case "8: loop already running -> silent" silent "$(mk_payload 'take this spec to pr' test-8)"
rm -rf .agentic-loop

echo ""
echo "==========================="
printf 'passed: %d   failed: %d\n' "$PASS" "$FAIL"
if [ "$FAIL" -gt 0 ]; then
  printf 'failed scenarios:\n'
  for n in "${FAILED_NAMES[@]}"; do printf '  - %s\n' "$n"; done
  exit 1
fi
echo "all scenarios passed"
