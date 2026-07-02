#!/usr/bin/env bash
# Same as run_behavioural.sh, but ALSO registers the agentic-loop deterministic
# gate hooks in the scratch repo's .claude/ so stage transitions are enforced
# deterministically (not model-only). Used to confirm the state-transition gate
# hard-stops the eval-13 interview bypass.
set -uo pipefail
ID="$1"; SLUG="$2"; BUDGET="$3"; PROMPT_FILE="$4"; OUT_DIR="$5"; shift 5
if [ "$#" -gt 0 ]; then EXTRA_ENV=("$@"); else EXTRA_ENV=(); fi

PLUGIN_ROOT="/Users/simontanna/Repos/github/agent-loop-plugin"
HOOKS_SRC="$PLUGIN_ROOT/skills/agentic-loop"
BASE="/tmp/agentic-loop-eval"
REPO="$BASE/run-$ID"; ORIGIN="$BASE/run-$ID-origin.git"; BRANCH="feat/$ID-$SLUG"

rm -rf "$REPO" "$ORIGIN"
cp -r "$BASE/template" "$REPO"
git init -q --bare "$ORIGIN"
cd "$REPO"
git remote add origin "$ORIGIN"; git push -q origin main
git checkout -q -b "$BRANCH"; git push -q -u origin "$BRANCH"

# --- Register the deterministic gate hooks in the scratch repo ---
mkdir -p .claude/hooks
cp "$HOOKS_SRC/setup/hooks/agentic-loop-check-state-transition.sh" .claude/hooks/
cp "$HOOKS_SRC/setup/hooks/agentic-loop-check-tasks-json.sh"       .claude/hooks/
cp "$HOOKS_SRC/setup/hooks/agentic-loop-check-pr-ready.sh"         .claude/hooks/
cp "$HOOKS_SRC/scripts/postooluse-context-check.sh"               .claude/hooks/ 2>/dev/null || true
chmod +x .claude/hooks/*.sh
cat > .claude/settings.json <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Write|Edit", "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/agentic-loop-check-tasks-json.sh" } ] },
      { "matcher": "Write|Bash", "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/agentic-loop-check-state-transition.sh" } ] },
      { "matcher": "Bash", "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/agentic-loop-check-pr-ready.sh" } ] }
    ]
  }
}
JSON
git add -A .claude && git commit -q -m "chore: register agentic-loop gate hooks (eval harness)"
git push -q origin "$BRANCH"
echo "[runner-hooks] registered gate hooks in $REPO/.claude"

mkdir -p "$OUT_DIR"; PROMPT="$(cat "$PROMPT_FILE")"
echo "[runner-hooks] eval $ID on $BRANCH (budget \$$BUDGET) — launching claude -p ..."
START=$(date +%s)
env \
  CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
  AGENTIC_MODE=headless AGENTIC_IO_ADAPTER=file AGENTIC_BASE_REF=main \
  AGENTIC_ISSUE="$ID" AGENTIC_BRANCH="$BRANCH" AGENTIC_SLUG="$SLUG" AGENTIC_AUTHOR=evalbot \
  ${EXTRA_ENV[@]+"${EXTRA_ENV[@]}"} \
  claude -p "$PROMPT" \
    --plugin-dir "$PLUGIN_ROOT" --dangerously-skip-permissions --model opus \
    --output-format stream-json --verbose --max-budget-usd "$BUDGET" \
  > "$OUT_DIR/transcript.jsonl" 2> "$OUT_DIR/stderr.log"
RC=$?; END=$(date +%s)
echo "[runner-hooks] claude exit=$RC  wall=$((END-START))s"
[ -d "$REPO/.agentic-loop" ] && cp -r "$REPO/.agentic-loop" "$OUT_DIR/agentic-loop-state"
git -C "$REPO" log --oneline main.."$BRANCH" > "$OUT_DIR/branch-commits.log" 2>/dev/null || true
find "$REPO/src" -type f > "$OUT_DIR/src-files.log" 2>/dev/null || true
# Surface any hook blocks captured in the transcript
grep -o "Blocked by agentic-loop state-transition gate" "$OUT_DIR/transcript.jsonl" | head -1 > "$OUT_DIR/hook-block-detected.txt" 2>/dev/null || true
python3 -c "import json,sys;json.dump({'wall_seconds':$((END-START)),'exit_code':$RC},open('$OUT_DIR/runner-timing.json','w'))"
echo "[runner-hooks] state -> $OUT_DIR/agentic-loop-state"; ls "$OUT_DIR/agentic-loop-state" 2>/dev/null || echo "NO state"