#!/usr/bin/env bash
# Sequentially run a curated batch of behavioural evals. Cheap discipline evals
# first (Stage-1 interview exits ~6 min), the full 4-stage pipeline last.
set -uo pipefail
WS="/Users/simontanna/Repos/github/agent-loop-plugin/skills/agentic-loop-workspace"
IT="$WS/iteration-1"
run() { # id slug budget dir
  echo "";echo "########## EVAL $1 ($2) budget \$$3 ##########"
  bash "$WS/run_behavioural.sh" "$1" "$2" "$3" "$IT/$4/prompt.txt" "$IT/$4/with_skill"
}
run 99 audit-log      6  eval-09-must-interview
run 13 delete-account 6  eval-13-product-decision
run 8  hello-name     15 eval-08-full-pipeline
echo "";echo "########## BATCH COMPLETE ##########"