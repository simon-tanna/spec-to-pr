#!/usr/bin/env bash
# Offline regression checks; live harness/install evaluations are explicit opt-ins.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 scripts/build-distribution.py --check
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s skills/agentic-loop/scripts/__tests__ -v
python3 -m unittest discover -s skills/agentic-loop-workspace/__tests__ -v
bash hooks/__tests__/test-nudge-hook.sh
bash skills/agentic-loop/setup/hooks/__tests__/test-agentic-hooks.sh
bash skills/agentic-loop/setup/hooks/__tests__/test-shared-gates.sh
