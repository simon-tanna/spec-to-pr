#!/usr/bin/env bash
# Harness-independent policy checks. No tool-event payloads are required.
set -euo pipefail
# Keep unexpected command failures inside the public 0/1/2 contract.
trap 'rc=$?; trap - EXIT; case "$rc" in 0|2) exit "$rc" ;; *) exit 1 ;; esac' EXIT
fail() { echo "check-gates: $*" >&2; exit 1; }
[ "$#" -gt 0 ] || fail 'expected state|tasks|tdd|pr-ready'
CHECK=$1; shift
RUN_DIR= TARGET_STATE= INPUT_MODE= INPUT_FILE=
while [ "$#" -gt 0 ]; do
  [ "$#" -ge 2 ] || fail "missing value for $1"
  case "$1" in
    --run-dir) RUN_DIR=$2 ;;
    --target-state) TARGET_STATE=$2 ;;
    --input-mode) INPUT_MODE=$2 ;;
    --input-file) INPUT_FILE=$2 ;;
    *) fail "unknown option: $1" ;;
  esac
  shift 2
done
[ -d "$RUN_DIR" ] || fail '--run-dir must name an existing directory'
command -v jq >/dev/null || fail 'jq is required'
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../setup/hooks/lib-gates.sh"
case "$CHECK" in
  state)
    [ -n "$TARGET_STATE" ] || fail '--target-state is required'
    [ -z "$INPUT_MODE$INPUT_FILE" ] || fail 'state does not accept proposed content'
    gate_state "$RUN_DIR" "$TARGET_STATE" ;;
  tasks|tdd)
    [ -z "$TARGET_STATE" ] || fail '--target-state is only valid for state'
    [[ "$INPUT_MODE" == document || "$INPUT_MODE" == fragment ]] || fail '--input-mode must be document or fragment'
    [ -f "$INPUT_FILE" ] && [ -r "$INPUT_FILE" ] || fail '--input-file must be readable'
    PROPOSED=$(cat "$INPUT_FILE")
    if [ "$CHECK" = tdd ]; then
      # Git traces must be resolved in the run's repository, not the caller's.
      cd "$RUN_DIR"
      gate_tdd "$INPUT_MODE" "$PROPOSED"
    else
      gate_tasks "$INPUT_MODE" "$PROPOSED"
    fi ;;
  pr-ready)
    [ -z "$TARGET_STATE$INPUT_MODE$INPUT_FILE" ] || fail 'pr-ready accepts only --run-dir'
    gate_pr_ready "$RUN_DIR" ;;
  *) fail "unknown check: $CHECK" ;;
esac
