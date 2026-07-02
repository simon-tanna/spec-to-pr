#!/usr/bin/env bash
# Behavioural eval runner for the agentic-loop skill.
#
# Runs one eval as a top-level `claude -p` subprocess (which CAN dispatch the
# loop's subagents — sidestepping the no-nested-subagent limit). Mode is
# headless + file adapter so there is no human to block on and no gh dependency:
# interviews/banners are written to .agentic-loop/<id>/notifications.md and the
# loop exits cleanly.
#
# Usage: run_behavioural.sh <id> <slug> <budget_usd> <prompt_file> <out_dir> [extra_env...]
set -uo pipefail

ID="$1"; SLUG="$2"; BUDGET="$3"; PROMPT_FILE="$4"; OUT_DIR="$5"; shift 5
# Guard empty-array expansion under `set -u` on bash 3.2 (macOS default).
if [ "$#" -gt 0 ]; then EXTRA_ENV=("$@"); else EXTRA_ENV=(); fi

# Resolve the plugin/repo root from this script's location (this file lives at
# <root>/skills/agentic-loop-workspace/), with an env override for odd layouts.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="${PLUGIN_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
BASE="/tmp/agentic-loop-eval"
REPO="$BASE/run-$ID"
ORIGIN="$BASE/run-$ID-origin.git"
BRANCH="feat/$ID-$SLUG"

rm -rf "$REPO" "$ORIGIN"
cp -r "$BASE/template" "$REPO"
# bare origin so git-sync.sh push succeeds
git init -q --bare "$ORIGIN"
cd "$REPO"
git remote add origin "$ORIGIN"
git push -q origin main
# The CI "Pin agentic-loop branch" step is simulated here: create + checkout the
# deterministic feature branch and publish it so pushes have an upstream.
git checkout -q -b "$BRANCH"
git push -q -u origin "$BRANCH"

mkdir -p "$OUT_DIR"
PROMPT="$(cat "$PROMPT_FILE")"

echo "[runner] eval $ID on $BRANCH (budget \$$BUDGET) — launching claude -p ..."
START=$(date +%s)

env \
  CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
  AGENTIC_MODE=headless \
  AGENTIC_IO_ADAPTER=file \
  AGENTIC_BASE_REF=main \
  AGENTIC_ISSUE="$ID" \
  AGENTIC_BRANCH="$BRANCH" \
  AGENTIC_SLUG="$SLUG" \
  AGENTIC_AUTHOR=evalbot \
  ${EXTRA_ENV[@]+"${EXTRA_ENV[@]}"} \
  claude -p "$PROMPT" \
    --plugin-dir "$PLUGIN_ROOT" \
    --dangerously-skip-permissions \
    --model opus \
    --output-format stream-json --verbose \
    --max-budget-usd "$BUDGET" \
  > "$OUT_DIR/transcript.jsonl" 2> "$OUT_DIR/stderr.log"
RC=$?
END=$(date +%s)
echo "[runner] claude exit=$RC  wall=$((END-START))s"

# Snapshot produced state for grading.
if [ -d "$REPO/.agentic-loop" ]; then
  cp -r "$REPO/.agentic-loop" "$OUT_DIR/agentic-loop-state"
fi
# Record what code (if any) landed, and the git log on the branch.
git -C "$REPO" log --oneline main.."$BRANCH" > "$OUT_DIR/branch-commits.log" 2>/dev/null || true
git -C "$REPO" diff --stat main.."$BRANCH" > "$OUT_DIR/branch-diffstat.log" 2>/dev/null || true
find "$REPO/src" -type f > "$OUT_DIR/src-files.log" 2>/dev/null || true
# Timing.
python3 - "$OUT_DIR" "$((END-START))" "$RC" <<'PY'
import json, sys
out, wall, rc = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
json.dump({"wall_seconds": wall, "exit_code": rc}, open(out+"/runner-timing.json","w"), indent=2)
PY
echo "[runner] state snapshot -> $OUT_DIR/agentic-loop-state"
ls "$OUT_DIR/agentic-loop-state" 2>/dev/null || echo "[runner] NO .agentic-loop state produced"