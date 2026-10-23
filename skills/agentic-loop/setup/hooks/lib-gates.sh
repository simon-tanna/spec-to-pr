#!/usr/bin/env bash
# Shared gate policies. Subshell functions preserve early exits without exiting callers.

gate_state() (
  DIR="$1"; NEW_STATE="$2"; ID="${DIR##*/}"
case "$NEW_STATE" in
  spec)
    exit 0
    ;;
  plan)
    # Stage 1 → Stage 2 gate. Symmetric with the `implement` gate below:
    # leaving the spec loop requires the structured spec-review to exist,
    # be machine-readable JSON, and be `approved` with no outstanding
    # interview. Past headless runs surfaced load-bearing questions and
    # then advanced straight to plan/implement under self-approved
    # "assumptions" without ever persisting a spec-review — the wording
    # fix halts that, and this is its deterministic backstop.
    MISSING=()
    [ -s "$DIR/spec.md" ]        || MISSING+=("$DIR/spec.md (non-empty)")
    [ -s "$DIR/spec-review.md" ] || MISSING+=("$DIR/spec-review.md (non-empty, JSON)")

    if [ -s "$DIR/spec-review.md" ]; then
      grep -qE '"verdict"\s*:\s*"approved"'    "$DIR/spec-review.md" || MISSING+=('spec-review.md verdict != "approved"')
      grep -qE '"force_interview"\s*:\s*false'  "$DIR/spec-review.md" || MISSING+=('spec-review.md force_interview != false')
    fi

    if [ -f "$DIR/open-questions.md" ] && [ -s "$DIR/open-questions.md" ]; then
      MISSING+=("$DIR/open-questions.md must be empty or absent before plan")
    fi

    [ ${#MISSING[@]} -eq 0 ] && exit 0

    {
      echo "Blocked by agentic-loop state-transition gate."
      echo ""
      echo "Cannot enter \`plan\` for #$ID. Missing Stage 1 preconditions:"
      for m in "${MISSING[@]}"; do
        echo "  • $m"
      done
      echo ""
      echo "Finish Stage 1 (spec loop) first. The structured spec-review MUST be"
      echo "saved verbatim as JSON to spec-review.md with verdict \"approved\" and"
      echo "force_interview false, and open-questions.md must be empty or absent."
      echo "A load-bearing decision surfaced during spec must be answered by the"
      echo "human before advancing — see the agentic-loop skill's references/interview-protocol.md."
    } >&2
    exit 2
    ;;
  implement)
    MISSING=()
    [ -s "$DIR/plan.md" ]        || MISSING+=("$DIR/plan.md (non-empty)")
    [ -s "$DIR/tasks.json" ]     || MISSING+=("$DIR/tasks.json (non-empty)")
    [ -s "$DIR/plan-review.md" ] || MISSING+=("$DIR/plan-review.md (non-empty)")

    if [ -s "$DIR/tasks.json" ]; then
      TASK_COUNT=$(jq '.tasks // [] | length' "$DIR/tasks.json" 2>/dev/null || echo 0)
      [ "$TASK_COUNT" -gt 0 ] || MISSING+=("$DIR/tasks.json must have non-empty tasks array")
    fi

    if [ -s "$DIR/plan-review.md" ]; then
      grep -qE '"verdict"\s*:\s*"approved"'   "$DIR/plan-review.md" || MISSING+=('plan-review.md verdict != "approved"')
      grep -qE '"critical"\s*:\s*\[\s*\]'     "$DIR/plan-review.md" || MISSING+=('plan-review.md critical not empty')
      grep -qE '"important"\s*:\s*\[\s*\]'    "$DIR/plan-review.md" || MISSING+=('plan-review.md important not empty')
    fi

    if [ -f "$DIR/open-questions.md" ] && [ -s "$DIR/open-questions.md" ]; then
      MISSING+=("$DIR/open-questions.md must be empty or absent before implement")
    fi

    [ ${#MISSING[@]} -eq 0 ] && exit 0

    {
      echo "Blocked by agentic-loop state-transition gate."
      echo ""
      echo "Cannot enter \`implement\` for #$ID. Missing preconditions:"
      for m in "${MISSING[@]}"; do
        echo "  • $m"
      done
      echo ""
      echo "Run Stage 2 per the agentic-loop skill's references/plan-loop.md."
      echo "The plan is the contract the implementer satisfies; without it"
      echo "there is no TDD baseline and review has nothing to check against."
    } >&2
    exit 2
    ;;
  done)
    [ -s "$DIR/tasks.json" ] || {
      echo "Blocked: cannot enter \`done\` without $DIR/tasks.json" >&2
      exit 2
    }

    if ! OFFENDERS=$(jq -r '
      .tasks // []
      | map(select(.status != "done"
          or (.spec_review_sha // "") == ""
          or (.quality_review_sha // "") == ""
          or (.blocker_count // 0) >= 2))
      | .[].id
    ' "$DIR/tasks.json" 2>&1); then
      {
        echo "Blocked by agentic-loop state-transition gate."
        echo ""
        echo "Could not parse $DIR/tasks.json:"
        echo "$OFFENDERS" | sed 's/^/  /'
      } >&2
      exit 2
    fi

    if [ -n "$OFFENDERS" ]; then
      {
        echo "Blocked by agentic-loop state-transition gate."
        echo ""
        echo "Cannot enter \`done\`. These tasks fail one or more gates:"
        while IFS= read -r id; do
          [ -z "$id" ] && continue
          echo "  • $id"
        done <<< "$OFFENDERS"
        echo ""
        echo "Possible causes per task:"
        echo "  • status != \"done\""
        echo "  • spec_review_sha or quality_review_sha empty"
        echo "  • blocker_count >= 2 with no intervening plan-loop revision"
        echo "    (reset semantics: see references/status-handling.md)"
      } >&2
      exit 2
    fi
    exit 0
    ;;
  *)
    {
      echo "Blocked: unknown .state value '$NEW_STATE'."
      echo "Valid values: spec | plan | implement | done"
    } >&2
    exit 2
    ;;
esac

)

gate_tasks() (
  INPUT_MODE="$1"; PROPOSED="$2"
if [[ "$INPUT_MODE" == "document" ]]; then
  CONTENT="$PROPOSED"

  # Validate JSON; if it doesn't parse let the actual write fail naturally.
  echo "$CONTENT" | jq empty >/dev/null 2>&1 || exit 0

  OFFENDERS=$(echo "$CONTENT" | jq -r '
    .tasks // []
    | map(select(.status == "done"
        and ((.spec_review_sha // "") == ""
             or (.quality_review_sha // "") == ""
             or (.blocker_count // 0) >= 2)))
    | .[].id
  ')

  if [ -n "$OFFENDERS" ]; then
    {
      echo "Blocked by agentic-loop tasks.json gate."
      echo ""
      echo "These tasks are marked status:\"done\" with one or more gate failures:"
      while IFS= read -r id; do
        [ -z "$id" ] && continue
        echo "  • $id"
      done <<< "$OFFENDERS"
      echo ""
      echo "Possible causes:"
      echo "  • spec_review_sha or quality_review_sha missing/empty —"
      echo "    run the missing review pass via code-reviewer."
      echo "  • blocker_count >= 2 — the task hit BLOCKED twice and must"
      echo "    round-trip through plan-loop revision (which resets"
      echo "    blocker_count to 0) before reaching done."
      echo ""
      echo "See the agentic-loop skill's references/execution-loop.md and"
      echo "the agentic-loop skill's references/status-handling.md."
    } >&2
    exit 2
  fi
  exit 0
fi

# Edit branch — fragment may not include surrounding fields. Conservative
# rule: any new_string introducing "status": "done" must include both
# review sha keys with non-empty values somewhere in the same fragment.
NEW="$PROPOSED"
[ -z "$NEW" ] && exit 0
echo "$NEW" | grep -qE '"status"\s*:\s*"done"' || exit 0

# Both review-sha keys must appear with non-empty string values in the fragment.
HAS_SPEC=$(echo "$NEW" | grep -cE '"spec_review_sha"\s*:\s*"[^"]+"' || true)
HAS_QUAL=$(echo "$NEW" | grep -cE '"quality_review_sha"\s*:\s*"[^"]+"' || true)

if [ "$HAS_SPEC" -eq 0 ] || [ "$HAS_QUAL" -eq 0 ]; then
  {
    echo "Blocked by agentic-loop tasks.json gate."
    echo ""
    echo "Edit introduces status:\"done\" without both review shas in the"
    echo "same fragment."
    echo ""
    echo "Either:"
    echo "  1. Run spec-compliance + code-quality reviews, populate both"
    echo "     spec_review_sha and quality_review_sha in the same Edit, OR"
    echo "  2. Use Write to overwrite the full tasks.json with the complete"
    echo "     task object including both shas."
    echo ""
    echo "See the agentic-loop skill's references/execution-loop.md."
  } >&2
  exit 2
fi

# blocker_count check: block ONLY when the fragment explicitly sets
# blocker_count to a value >= 2 alongside status="done". Absence of
# blocker_count from the fragment is allowed (partial edit — the on-disk
# value governs and other hooks read it from disk).
BLOCKER_HIGH=$(echo "$NEW" | grep -cE '"blocker_count"\s*:\s*([2-9]|[1-9][0-9]+)([^0-9]|$)' || true)

if [ "$BLOCKER_HIGH" -gt 0 ]; then
  {
    echo "Blocked by agentic-loop tasks.json gate."
    echo ""
    echo "Edit sets status:\"done\" while explicitly setting blocker_count >= 2."
    echo "A task that hit BLOCKED twice must round-trip through plan-loop"
    echo "revision (which resets blocker_count to 0) before reaching done."
    echo ""
    echo "See the agentic-loop skill's references/status-handling.md."
  } >&2
  exit 2
fi

exit 0

)

gate_tdd() (
  INPUT_MODE="$1"; PROPOSED="$2"
TEST_PATH_RE='(\.test\.|\.spec\.|_test\.|_spec\.|/__tests__/|(^|/)tests?/|(^|/)test_)'
# Verify one commit: prints nothing if OK, else prints the reason(s).
# $1 = commit sha. Only called for non-empty, resolvable shas.
commit_trace_problems() {
  local sha="$1" problems=""
  local body files
  body=$(git show -s --format=%B "$sha" 2>/dev/null || true)
  files=$(git show --name-only --format='' "$sha" 2>/dev/null || true)

  echo "$body" | grep -qE '(^|[^A-Za-z])TDD:' || problems+="no \`TDD:\` line in commit message; "
  echo "$files" | grep -qE "$TEST_PATH_RE" || problems+="no test file in commit diff; "

  printf '%s' "$problems"
}

# Resolve a sha to a commit object; empty/unresolvable → return 1 (skip).
resolvable() {
  local sha="$1"
  [ -n "$sha" ] || return 1
  git cat-file -e "${sha}^{commit}" 2>/dev/null || return 1
}

if [[ "$INPUT_MODE" == "document" ]]; then
  CONTENT="$PROPOSED"
  # If it doesn't parse, let the real write fail naturally.
  echo "$CONTENT" | jq empty >/dev/null 2>&1 || exit 0

  # id \t commit_sha, for every done task.
  DONE_TASKS=$(echo "$CONTENT" | jq -r '
    .tasks // []
    | map(select(.status == "done"))
    | .[] | [.id, (.commit_sha // "")] | @tsv
  ')

  OFFENDERS=""
  while IFS=$'\t' read -r id sha; do
    [ -z "$id" ] && continue
    resolvable "$sha" || continue
    problems=$(commit_trace_problems "$sha")
    [ -n "$problems" ] && OFFENDERS+="  • $id ($sha): ${problems%; }"$'\n'
  done <<< "$DONE_TASKS"

  if [ -n "$OFFENDERS" ]; then
    {
      echo "Blocked by agentic-loop TDD-trace gate."
      echo ""
      echo "These tasks are marked status:\"done\" but their commit fails the"
      echo "TDD-trace check:"
      printf '%s' "$OFFENDERS"
      echo ""
      echo "Every task's atomic commit MUST contain the test file it was written"
      echo "against AND a \`TDD:\` line in the message body citing that test"
      echo "(e.g. 'TDD: __tests__/foo.test.ts:12-30 written before implementation')."
      echo "Re-commit the task with the test included and the TDD: trace, then retry."
      echo ""
      echo "See the agentic-loop skill's references/tdd.md and references/execution-loop.md."
    } >&2
    exit 2
  fi
  exit 0
fi

# Edit branch — conservative: only act when the fragment itself introduces
# status:"done" AND carries a resolvable commit_sha. Partial edits without a
# sha pass (the on-disk Write path / tasks-json gate govern).
NEW="$PROPOSED"
[ -z "$NEW" ] && exit 0
echo "$NEW" | grep -qE '"status"\s*:\s*"done"' || exit 0

SHA=$(echo "$NEW" | grep -oE '"commit_sha"\s*:\s*"[0-9a-fA-F]{7,40}"' | head -1 \
  | grep -oE '[0-9a-fA-F]{7,40}' || true)
resolvable "$SHA" || exit 0

problems=$(commit_trace_problems "$SHA")
if [ -n "$problems" ]; then
  {
    echo "Blocked by agentic-loop TDD-trace gate."
    echo ""
    echo "Edit marks a task status:\"done\" but its commit ($SHA) fails the"
    echo "TDD-trace check: ${problems%; }."
    echo ""
    echo "The task's atomic commit MUST contain its test file AND a \`TDD:\` line"
    echo "in the message body. Re-commit with the test + TDD: trace, then retry."
    echo ""
    echo "See the agentic-loop skill's references/tdd.md."
  } >&2
  exit 2
fi

exit 0

)

gate_pr_ready() (
  DIR="$1"
REASONS=()

if [ -s "$DIR/tasks.json" ]; then
  JQ_ERR=$(mktemp)
  JQ_STATUS=0
  OFFENDERS=$(jq -r '
    .tasks // []
    | map(select(.status != "done"
        or (.spec_review_sha // "") == ""
        or (.quality_review_sha // "") == ""
        or (.blocker_count // 0) >= 2))
    | .[].id
  ' "$DIR/tasks.json" 2>"$JQ_ERR") || JQ_STATUS=$?

  if [ "$JQ_STATUS" -ne 0 ]; then
    REASONS+=("$DIR/tasks.json failed to parse (jq exit $JQ_STATUS):")
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      REASONS+=("    $line")
    done < "$JQ_ERR"
  elif [ -n "$OFFENDERS" ]; then
    REASONS+=("incomplete tasks in $DIR/tasks.json:")
    while IFS= read -r id; do
      [ -z "$id" ] && continue
      REASONS+=("    • $id")
    done <<< "$OFFENDERS"
  fi

  rm -f "$JQ_ERR"
else
  REASONS+=("$DIR/tasks.json missing or empty")
fi

if [ -f "$DIR/open-questions.md" ] && [ -s "$DIR/open-questions.md" ]; then
  REASONS+=("$DIR/open-questions.md is non-empty — interview not closed")
fi

[ ${#REASONS[@]} -eq 0 ] && exit 0

{
  echo "Blocked by agentic-loop PR-ready gate."
  echo ""
  echo "Cannot \`gh pr create\` for $DIR. Reasons:"
  for r in "${REASONS[@]}"; do
    echo "  • $r"
  done
  echo ""
  echo "Finish all tasks (status:done, both review shas populated, and"
  echo "blocker_count < 2 — reset by plan-loop revision if it ever hit 2),"
  echo "and resolve any open questions before opening the PR."
  echo "See the agentic-loop skill's references/ship.md and"
  echo "the agentic-loop skill's references/status-handling.md."
} >&2
exit 2

)
