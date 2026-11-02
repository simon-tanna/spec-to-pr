#!/usr/bin/env bash
# Offline regression checks; live harness/install evaluations are explicit opt-ins.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 scripts/build-distribution.py --check
# Behavioural schema tests need jsonschema; run them through uv when available
# (no runtime dependency) and let them skip otherwise.
if command -v uv >/dev/null 2>&1; then
  uv run --no-project --quiet --with jsonschema python3 -m unittest discover -s tests -v
else
  echo "uv not found: jsonschema-backed schema tests will be skipped" >&2
  python3 -m unittest discover -s tests -v
fi
python3 -m unittest discover -s skills/agentic-loop/scripts/__tests__ -v
bash hooks/__tests__/test-nudge-hook.sh
bash skills/agentic-loop/setup/hooks/__tests__/test-agentic-hooks.sh
bash skills/agentic-loop/setup/hooks/__tests__/test-shared-gates.sh
