#!/usr/bin/env bash
# Initialize an interactive run. No commit, push, stash, reset, or remote mutation.
set -euo pipefail
fail() { printf 'init-run: %s\n' "$*" >&2; exit 1; }
# Keep PR base metadata a branch name; checkout may use a qualified local ref.
normalize_base() {
  local value="$1"
  case "$value" in
    refs/heads/*) value=${value#refs/heads/} ;;
    refs/remotes/origin/*) value=${value#refs/remotes/origin/} ;;
    origin/*) value=${value#origin/} ;;
    refs/*) fail 'Base must be a branch on origin, not another ref namespace' ;;
  esac
  [[ -n "$value" && "$value" != -* && "$value" != HEAD ]] || fail 'Invalid base branch'
  git check-ref-format "refs/heads/$value" >/dev/null 2>&1 || fail 'Invalid base branch'
  printf '%s\n' "$value"
}
resolve_base_start() {
  local value="$1" remote_match
  if git show-ref --verify --quiet "refs/heads/$value"; then
    printf 'refs/heads/%s\n' "$value"
  elif git show-ref --verify --quiet "refs/remotes/origin/$value"; then
    remote_match=$(git ls-remote --heads origin "refs/heads/$value") || fail 'Cannot inspect remote base branch'
    [[ -n "$remote_match" ]] || fail 'Base remote-tracking reference has no branch on origin'
    printf 'refs/remotes/origin/%s\n' "$value"
  else
    fail "Base branch unavailable locally: $value (fetch origin first)"
  fi
}
source_file='' title='' issue=''  explicit_base='' issue_base='' label_base='' requested_id='' requested_branch=''
while [[ $# -gt 0 ]]; do
  [[ $# -ge 2 && -n "$2" ]] || fail "Expected a value for $1"
  case "$1" in
    --source-file) source_file=$2;; --title) title=$2;; --issue) issue=$2;;
    --base-ref) explicit_base=$2;; --issue-base) issue_base=$2;; --label-base) label_base=$2;;
    --run-id) requested_id=$2;; --branch) requested_branch=$2;;
    *) fail "Unknown option: $1";;
  esac
  shift 2
done
command -v jq >/dev/null || fail 'jq is required'
[[ -f "$source_file" ]] || fail '--source-file must name a readable regular file'
source_file="$(cd "$(dirname "$source_file")" && pwd -P)/$(basename "$source_file")"
repo=$(git rev-parse --show-toplevel 2>/dev/null) || fail 'Run inside a Git worktree'
cd "$repo"
[[ -z "$explicit_base" ]] || explicit_base=$(normalize_base "$explicit_base")
current_branch=$(git symbolic-ref --quiet --short HEAD) || fail 'Detached HEAD is unsupported'
[[ -z "$issue" || "$issue" =~ ^[1-9][0-9]*$ ]] || fail 'Issue must be a positive integer'
[[ -z "$requested_id" || "$requested_id" =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]*$ ]] || fail 'Invalid run ID'
if command -v sha256sum >/dev/null; then
  source_hash=$(sha256sum < "$source_file" | awk '{print $1}')
else
  source_hash=$(shasum -a 256 < "$source_file" | awk '{print $1}')
fi
[[ -n "$title" ]] || title=$(basename "$source_file")
title=${title%.md}
slug=$(printf '%s' "$title" | LC_ALL=C tr '[:upper:]' '[:lower:]' | LC_ALL=C sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' | cut -c1-40 | sed 's/-*$//')
[[ -n "$slug" ]] || slug=spec
run_id=${issue:-$slug-${source_hash:0:8}}
if [[ -n "$requested_id" ]]; then run_id=$requested_id; fi
run_dir=".agentic-loop/$run_id"
metadata="$run_dir/run-context.json"
[[ ! -L .agentic-loop && ! -L "$run_dir" && ! -L "$metadata" ]] || fail 'Run storage must not be a symlink'
# Preflight remains read-only: ls-remote does not update local refs or remote data.
git remote get-url origin >/dev/null 2>&1 || fail 'Configure origin before initialization'
git ls-remote origin >/dev/null 2>&1 || fail 'Origin is unreachable'
if [[ -f "$metadata" ]]; then
  jq -e --arg id "$run_id" --arg hash "$source_hash" '.schema_version == 1 and .run_id == $id and .source_hash == $hash and (.branch | type == "string") and (.base_ref | type == "string")' "$metadata" >/dev/null || fail 'Persisted run identity/source mismatch'
  branch=$(jq -r '.branch' "$metadata")
  base=$(jq -r '.base_ref' "$metadata")
  [[ "$current_branch" == "$branch" ]] || fail "Resume requires branch $branch; select it explicitly"
  [[ -z "$requested_branch" || "$requested_branch" == "$branch" ]] || fail 'Cannot change branch on resume'
  [[ -z "$explicit_base" || "$explicit_base" == "$base" ]] || fail 'Cannot change base on resume'
  [[ -z "$issue" || "$(jq -r '.issue // ""' "$metadata")" == "$issue" ]] || fail 'Cannot change issue on resume'
  [[ ! -L "$run_dir/source.md" ]] && cmp -s "$source_file" "$run_dir/source.md" || fail 'Persisted source mismatch'
  [[ "$base" == "$(normalize_base "$base")" ]] || fail 'Persisted base must be a normalized branch name'
  resolve_base_start "$base" >/dev/null
  jq '. + {resumed: true}' "$metadata"
  exit 0
fi
[[ -z "$requested_id" ]] || fail 'Requested resume ID has no metadata; choose an existing run explicitly'
[[ ! -e "$run_dir" ]] || fail 'Run directory exists without matching metadata'
git diff --quiet --ignore-submodules=none && git diff --cached --quiet --ignore-submodules=none || fail 'Fresh initialization requires a clean tracked worktree and index'
config_base=''
if [[ -f .agentic-loop.config.json ]]; then
  config_base=$(jq -er 'if .base_ref == null then "" elif (.base_ref | type) == "string" then .base_ref else error("base_ref must be a string") end' .agentic-loop.config.json) || fail 'Invalid config'
fi
base=${explicit_base:-${config_base:-${issue_base:-${label_base:-main}}}}
base=$(normalize_base "$base")
base_start=$(resolve_base_start "$base")
# Checkout can introduce storage paths absent from the current worktree. Inspect
# the selected base tree before changing branches, preventing symlink traversal
# and overwrites of an unrelated run already tracked on that base.
base_storage=$(git ls-tree "$base_start" -- .agentic-loop)
if [[ -n "$base_storage" && "$base_storage" != "040000 tree "* ]]; then
  fail 'Base contains non-directory run storage'
fi
[[ -z "$(git ls-tree "$base_start" -- "$run_dir")" ]] || fail 'Base already contains the selected run directory'
if [[ -n "$issue" ]]; then branch="feat/$issue-$slug"; else branch="feat/$run_id"; fi
branch=${requested_branch:-$branch}
git check-ref-format --branch "$branch" >/dev/null 2>&1 || fail 'Invalid feature branch'
[[ "$branch" == feat/* && "$branch" != "$base" ]] || fail 'Feature branch must be under feat/ and differ from base'
if git show-ref --verify --quiet "refs/heads/$branch"; then
  fail 'Branch exists without matching persisted run metadata'
fi
remote_branch=$(git ls-remote --heads origin "refs/heads/$branch") || fail 'Cannot inspect remote feature branch'
[[ -z "$remote_branch" ]] || fail 'Remote branch exists without matching persisted run metadata'
# Snapshot input before checkout: a tracked input may not exist on the base branch.
source_snapshot=$(mktemp "${TMPDIR:-/tmp}/agentic-source.XXXXXX")
trap 'rm -f "$source_snapshot"' EXIT
cp "$source_file" "$source_snapshot"
# All expected preflight failures occur before any mutation.
git checkout -b "$branch" "$base_start" >&2
# Recheck the materialized tree as well (including changes from checkout hooks).
[[ ! -L .agentic-loop && ! -e "$run_dir" && ! -L "$run_dir" ]] || fail 'Run storage changed during checkout; no run files written'
[[ ! -e .agentic-loop || -d .agentic-loop ]] || fail 'Run storage is not a directory'
mkdir -p "$run_dir"
cp "$source_snapshot" "$run_dir/source.md"
jq -n --arg id "$run_id" --arg dir "$run_dir" --arg path "$source_file" --arg hash "$source_hash" --arg branch "$branch" --arg base "$base" --arg issue "$issue" \
  '{schema_version: 1, run_id: $id, run_dir: $dir, source_path: $path, source_hash: $hash, branch: $branch, base_ref: $base, issue: (if $issue == "" then null else $issue end)}' > "$metadata"
jq '. + {resumed: false}' "$metadata"
