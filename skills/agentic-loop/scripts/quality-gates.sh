#!/usr/bin/env bash
# Quality gates for the agentic-loop skill — repo-agnostic.
#
# Resolution order for each gate (test, lint, typecheck, build):
#   1. .agentic-loop.config.json -> .quality_gates.<name>  (non-empty = run; "" = explicit skip)
#   2. auto-detect from the toolchain (package.json scripts via the lockfile's package manager;
#      else cargo/go/pytest for the `test` gate)
# Records the resolved set to ./.agentic-resolved-gates (one "name<TAB>command" per line) so the
# PR renderer reports only the gates that actually ran.
#
# Exits non-zero on: any gate failure; OR no gate resolvable at all; OR a JS project with no
# resolvable `test` gate that was not explicitly acknowledged. The loop treats non-zero as
# "must fix or confirm before shipping" — it must NEVER silently ship a PR with zero verification.
# The single escape hatch is an explicit "quality_gates": {} in the config (full opt-out).

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

CONFIG="$REPO_ROOT/.agentic-loop.config.json"
RESOLVED="$REPO_ROOT/.agentic-resolved-gates"

log()  { printf '\n\033[1;34m[quality-gates]\033[0m %s\n' "$*"; }
warn() { printf '\n\033[1;33m[quality-gates WARN]\033[0m %s\n' "$*" >&2; }
fail() { printf '\n\033[1;31m[quality-gates FAIL]\033[0m %s\n' "$*" >&2; exit 1; }

: >"$RESOLVED"   # truncate / regenerate every run

GATE_NAMES=(test lint typecheck build)
have_jq=0; command -v jq >/dev/null 2>&1 && have_jq=1
config_has_gates=0
opt_out=0

# config_gate <name>: prints the configured command, or the sentinel __UNSET__ when the key is
# absent. An empty result (key present, value "") means "explicitly skip this gate".
config_gate() {
  jq -r --arg k "$1" '
    if (.quality_gates | type) == "object" and (.quality_gates | has($k))
    then .quality_gates[$k] else "__UNSET__" end
  ' "$CONFIG"
}

if [ -f "$CONFIG" ] && [ "$have_jq" -eq 1 ]; then
  if jq -e '(.quality_gates | type) == "object"' "$CONFIG" >/dev/null 2>&1; then
    config_has_gates=1
    [ "$(jq -r '.quality_gates | length' "$CONFIG")" = "0" ] && opt_out=1
  fi
fi

log "repo: $REPO_ROOT"

if [ "$opt_out" -eq 1 ]; then
  log 'config sets "quality_gates": {} — gates explicitly opted out; recording none.'
  printf '# gates opted out via .agentic-loop.config.json\n' >>"$RESOLVED"
  exit 0
fi

# Package manager for JS projects (empty if not a JS project).
detect_pm() {
  if   [ -f pnpm-lock.yaml ];    then echo pnpm
  elif [ -f yarn.lock ];         then echo yarn
  elif [ -f bun.lockb ];         then echo bun
  elif [ -f package-lock.json ]; then echo npm
  elif [ -f package.json ];      then echo npm
  else echo ""; fi
}

pkg_has_script() {
  [ -f package.json ] && [ "$have_jq" -eq 1 ] && \
    [ -n "$(jq -r --arg s "$1" '.scripts[$s] // empty' package.json)" ]
}

PM="$(detect_pm)"

# resolve_gate <name>: echoes the command to run, or empty string (skip). Config wins (including
# an explicit "" skip); otherwise auto-detect. `<pm> run <name>` is uniform across npm/pnpm/yarn/bun.
resolve_gate() {
  local name="$1" cfg
  if [ "$config_has_gates" -eq 1 ]; then
    cfg="$(config_gate "$name")"
    if [ "$cfg" != "__UNSET__" ]; then printf '%s' "$cfg"; return 0; fi
  fi
  if [ -n "$PM" ]; then
    pkg_has_script "$name" && printf '%s run %s' "$PM" "$name"
    return 0
  fi
  if [ "$name" = "test" ]; then
    if   [ -f Cargo.toml ]; then printf 'cargo test'
    elif [ -f go.mod ];     then printf 'go test ./...'
    elif [ -f pyproject.toml ] || [ -f pytest.ini ] || [ -f setup.cfg ]; then printf 'pytest'
    fi
  fi
  return 0
}

# Was the `test` gate explicitly acknowledged in config (a command OR an explicit "" skip)?
test_acked=0
if [ "$config_has_gates" -eq 1 ] && [ "$(config_gate test)" != "__UNSET__" ]; then
  test_acked=1
fi

ran_any=0
for g in "${GATE_NAMES[@]}"; do
  cmd="$(resolve_gate "$g")"
  if [ -z "$cmd" ]; then
    log "gate '$g': none configured/detected — skipping"
    continue
  fi
  log "running $g: $cmd"
  bash -c "$cmd" 2>&1 || fail "$g gate failed: $cmd"
  printf '%s\t%s\n' "$g" "$cmd" >>"$RESOLVED"
  ran_any=1
done

# Safety: a JS project with no `test` gate and no explicit acknowledgement must not ship.
if [ -n "$PM" ] && [ -z "$(resolve_gate test)" ] && [ "$test_acked" -eq 0 ]; then
  fail "JS project detected ($PM) but no 'test' script found, and config did not acknowledge it.
Refusing to ship untested code. Add a 'test' script, or set \"quality_gates\": {\"test\": \"\"} in
.agentic-loop.config.json to skip it explicitly."
fi

# Safety: never report success when nothing ran.
if [ "$ran_any" -eq 0 ]; then
  fail "No quality gate could be resolved for this repo. Refusing to ship with zero verification.
Add test/lint/typecheck commands to .agentic-loop.config.json, or set \"quality_gates\": {} to opt
out explicitly. (In interactive mode the controller confirms this via AskUserQuestion; in CI it
posts a blocking comment and exits — see SKILL.md 'Quality gates'.)"
fi

log "all resolved gates green"
