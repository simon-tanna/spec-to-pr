#!/usr/bin/env bash
# Iteration-3 re-eval: confirm the three post-eval improvements behaviourally.
# All three runs register the gate hooks so the NEW gates are live:
#   • eval 6  — asserts spec.md now emits BOTH §8 Resolved Decisions AND §10 Risks,
#               and that the new Stage 1→2 `plan` gate ALLOWS a legit spec-lock.
#   • eval 8  — full 4-stage pipeline with the new TDD-trace hook registered;
#               asserts the task completes and the hook passes (no regression).
#   • eval 13 — asserts the loop still halts at spec; then an in-situ skip-probe
#               confirms the `plan` gate deterministically BLOCKS a manual
#               `.state=plan` while open-questions is non-empty.
set -uo pipefail
WS="/Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace"
IT="$WS/iteration-3"
PLUGIN="/Users/simontanna/Repos/github/agent-loop-plugin"
STATE_HOOK="$PLUGIN/skills/agentic-loop/setup/hooks/agentic-loop-check-state-transition.sh"

echo "";echo "########## RUN 1: eval 6 + hooks — §8 Resolved Decisions + §10 Risks, plan-gate happy path ##########"
bash "$WS/run_behavioural_hooks.sh" 6  hello-fn       6  "$IT/eval-06-risks/prompt.txt"     "$IT/eval-06-risks/with_skill"

echo "";echo "########## RUN 2: eval 8 + hooks — full pipeline with TDD-trace hook ##########"
bash "$WS/run_behavioural_hooks.sh" 8  hello-name     15 "$IT/eval-08-pipeline/prompt.txt"  "$IT/eval-08-pipeline/with_skill"

echo "";echo "########## RUN 3: eval 13 + hooks — interview halt, then plan-gate skip-probe ##########"
bash "$WS/run_behavioural_hooks.sh" 13 delete-account 8  "$IT/eval-13-plan-gate/prompt.txt" "$IT/eval-13-plan-gate/with_skill"

echo "";echo "----- in-situ skip-probe: attempt .state=plan in the halted eval-13 scratch repo -----"
REPO="/tmp/agentic-loop-eval/run-13"
if [ -d "$REPO/.agentic-loop/13" ]; then
  PROBE=$(cd "$REPO" && printf '%s' \
    '{"tool_name":"Write","tool_input":{"file_path":".agentic-loop/13/.state","content":"plan"}}' \
    | bash "$STATE_HOOK" >/dev/null 2>&1; echo $?)
  if [ "$PROBE" = "2" ]; then
    echo "PASS ✓ plan gate BLOCKED the premature .state=plan (exit 2) — deterministic backstop works"
  else
    echo "CHECK ✗ expected exit 2 (block), got exit $PROBE — inspect $REPO/.agentic-loop/13"
  fi
else
  echo "SKIP — $REPO/.agentic-loop/13 not found (run 3 may not have produced state)"
fi

echo "";echo "########## ITERATION-3 RE-EVAL COMPLETE ##########"
echo "Grade with: inspect each with_skill/agentic-loop-state/<id>/ —"
echo "  eval 6:  spec.md contains '## §8 Resolved Decisions' AND '## §10 Risks'"
echo "  eval 8:  tasks.json task done; TDD: line + test file in the commit; .state=implement; SHIP_READY"
echo "  eval 13: .state=spec; open-questions.md non-empty; no plan.md/code; skip-probe PASS above"
