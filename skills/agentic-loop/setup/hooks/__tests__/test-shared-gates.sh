#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
CLI="$ROOT/scripts/check-gates.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/.agentic-loop/99" "$TMP/installed"
RUN="$TMP/.agentic-loop/99"
expect() {
  local want=$1; shift
  local got=0
  "$@" >"$TMP/output" 2>&1 || got=$?
  if [ "$want" != "$got" ]; then cat "$TMP/output"; echo "expected $want, got $got: $*"; exit 1; fi
}
printf '%s' '{broken' > "$TMP/input"
expect 0 bash "$CLI" tasks --run-dir "$RUN" --input-mode document --input-file "$TMP/input"
printf '%s' '"status":"done"' > "$TMP/input"
expect 2 bash "$CLI" tasks --run-dir "$RUN" --input-mode fragment --input-file "$TMP/input"
printf '%s' '"status":"done","spec_review_sha":"a","quality_review_sha":"b"' > "$TMP/input"
expect 0 bash "$CLI" tasks --run-dir "$RUN" --input-mode fragment --input-file "$TMP/input"
printf '%s' '{"tasks":[{"id":"a","status":"done","commit_sha":"0000000000000000000000000000000000000000"}]}' > "$TMP/input"
expect 0 bash "$CLI" tdd --run-dir "$RUN" --input-mode document --input-file "$TMP/input"
expect 2 bash "$CLI" tasks --run-dir "$RUN" --input-mode document --input-file "$TMP/input"
expect 2 bash "$CLI" state --run-dir "$RUN" --target-state implement
expect 2 bash "$CLI" pr-ready --run-dir "$RUN"
expect 1 bash "$CLI" tasks --run-dir "$RUN"
expect 1 bash "$CLI" state --run-dir "$RUN" --target-state spec --unexpected ignored
# Installed wrappers must depend only on sibling resources, not the checkout.
mkdir -p "$TMP/package/setup/hooks"
cp "$ROOT"/setup/hooks/agentic-loop-check-*.sh "$ROOT/setup/hooks/lib-gates.sh" "$TMP/package/setup/hooks/"
cp "$TMP/package/setup/hooks/"*.sh "$TMP/installed/"
rm -rf "$TMP/package"
cd "$TMP"
jq -n '{tool_name:"Write",tool_input:{file_path:".agentic-loop/99/tasks.json",content:"{\"tasks\":[{\"id\":\"a\",\"status\":\"done\"}]}"}}' > payload
expect 2 bash installed/agentic-loop-check-tasks-json.sh < payload
expect 0 bash "$ROOT/scripts/check-substrate.sh" --harness codex
if ! grep -q 'controller-invoked' "$TMP/output"; then cat "$TMP/output"; exit 1; fi
if grep -q 'deterministically enforced' "$TMP/output"; then exit 1; fi
# Complete checks run from a different caller directory still resolve run Git traces.
git init -q "$TMP"
git config user.email fixture@example.invalid
git config user.name fixture
printf 'test' > test_gate.txt
git add test_gate.txt
git commit -qm 'fixture: TDD: test_gate.txt'
SHA=$(git rev-parse HEAD)
printf '{"tasks":[{"id":"a","status":"done","commit_sha":"%s","spec_review_sha":"a","quality_review_sha":"b"}]}' "$SHA" > "$RUN/tasks.json"
expect 0 bash "$CLI" tdd --run-dir "$RUN" --input-mode document --input-file "$RUN/tasks.json"
expect 0 bash "$CLI" state --run-dir "$RUN" --target-state done
expect 0 bash "$CLI" pr-ready --run-dir "$RUN"
printf 'source' > source.txt
git add source.txt
git commit -qm 'fixture without trace'
BAD_SHA=$(git rev-parse HEAD)
printf '{"tasks":[{"id":"a","status":"done","commit_sha":"%s"}]}' "$BAD_SHA" > "$TMP/input"
expect 2 bash "$CLI" tdd --run-dir "$RUN" --input-mode document --input-file "$TMP/input"
printf '"status":"done","commit_sha":"%s"' "$BAD_SHA" > "$TMP/input"
expect 2 bash "$CLI" tdd --run-dir "$RUN" --input-mode fragment --input-file "$TMP/input"
printf '{"tasks":5}' > "$TMP/input"
expect 1 bash "$CLI" tasks --run-dir "$RUN" --input-mode document --input-file "$TMP/input"
# Copy the whole documented gate installation, then exercise only installed files.
mkdir -p .claude/hooks
cp "$TMP/installed/"*.sh .claude/hooks/
chmod +x .claude/hooks/*.sh
cp "$ROOT/setup/settings.snippet.json" .claude/settings.json
expect 0 bash "$ROOT/scripts/check-substrate.sh"
rm .claude/hooks/lib-gates.sh
expect 1 bash "$ROOT/scripts/check-substrate.sh" --harness claude
expect 0 bash "$ROOT/scripts/check-substrate.sh" --harness codex
cp "$TMP/installed/lib-gates.sh" .claude/hooks/
expect 0 bash "$ROOT/scripts/check-substrate.sh" --harness claude
# Upgrading copies wrappers and helper together; source may be unavailable afterwards.
expect 2 bash .claude/hooks/agentic-loop-check-tasks-json.sh < payload
printf '{"tasks":[{"id":"a","status":"done","spec_review_sha":"a","quality_review_sha":"b"}]}' > "$RUN/tasks.json"
jq -n '{tool_name:"Write",tool_input:{file_path:".agentic-loop/99/.state",content:"done"}}' > payload
expect 0 bash .claude/hooks/agentic-loop-check-state-transition.sh < payload
jq -n '{tool_name:"Bash",tool_input:{command:"gh pr create"}}' > payload
expect 0 bash .claude/hooks/agentic-loop-check-pr-ready.sh < payload
jq -n --arg sha "$BAD_SHA" '{tool_name:"Write",tool_input:{file_path:".agentic-loop/99/tasks.json",content:({tasks:[{id:"a",status:"done",commit_sha:$sha}]}|tojson)}}' > payload
expect 2 bash .claude/hooks/agentic-loop-check-tdd-trace.sh < payload
echo 'shared gates: policy, CLI contract, installed wrappers, helper upgrade and harness probes passed'
