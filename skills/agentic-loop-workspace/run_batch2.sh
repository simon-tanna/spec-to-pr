#!/usr/bin/env bash
# Iteration-2 confirmation: eval 13 (reworded skill) WITH hooks and WITHOUT hooks.
set -uo pipefail
WS="/Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace"
IT="$WS/iteration-2"
echo "";echo "########## RUN A: eval 13 + gate hooks (reworded skill) ##########"
bash "$WS/run_behavioural_hooks.sh" 13   delete-account 8 "$IT/eval-13h-hooks/prompt.txt"   "$IT/eval-13h-hooks/with_skill"
echo "";echo "########## RUN B: eval 13 NO hooks (reworded skill, wording-only) ##########"
bash "$WS/run_behavioural.sh"       1300 delete-account 8 "$IT/eval-13n-nohooks/prompt.txt" "$IT/eval-13n-nohooks/with_skill"
echo "";echo "########## CONFIRMATION BATCH COMPLETE ##########"
