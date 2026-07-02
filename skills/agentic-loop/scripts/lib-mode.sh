#!/usr/bin/env bash
# Shared interactivity-axis resolver for the agentic-loop skill.
#
# Prints exactly one word: "interactive" | "headless" — the answer to "can I
# block on a human?". GitHub Actions is ONE headless harness, not the definition
# of headless; this resolver lets the loop run AFK in any headless environment
# (a Cloudflare Sandbox/Container, a self-hosted runner, the Agent SDK, ...).
#
# Precedence (most explicit wins), defaulting to interactive so existing local
# Claude Code sessions behave exactly as before:
#   1. $AGENTIC_MODE ∈ {interactive, headless}   (explicit override)
#   2. $AGENTIC_HEADLESS ∈ {1, true, yes}        (explicit headless opt-in)
#   3. $GITHUB_ACTIONS == "true"                 (backward compat)
#   4. $CI == "true"                             (generic CI)
#   5. interactive
#
# TTY-absence is deliberately NOT a signal: Claude Code's Bash tool runs without
# a controlling TTY even in local interactive sessions, so keying on it would
# misclassify every local run as headless.

set -euo pipefail

case "${AGENTIC_MODE:-}" in
  interactive|headless) printf '%s' "$AGENTIC_MODE"; exit 0 ;;
esac
case "${AGENTIC_HEADLESS:-}" in
  1|true|yes) printf 'headless'; exit 0 ;;
esac
[ "${GITHUB_ACTIONS:-}" = "true" ] && { printf 'headless'; exit 0; }
[ "${CI:-}" = "true" ]            && { printf 'headless'; exit 0; }
printf 'interactive'
