#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_dir/skills"
agents_skills="$HOME/.agents/skills"
claude_commands="$HOME/.claude/commands"
openclaw_codex_skills="$HOME/.openclaw/acpx/codex-home/skills"
status=0
strict=1
verbose=0

usage() {
  cat <<'EOF'
Usage: audit-agent-skill-hosts.sh [--strict|--lenient] [--verbose]

Audits the shared local skill source across agent hosts:
  - repository truth source and Claude/Codex bridges
  - OpenClaw Codex HOME bridge
  - Claude Code slash command bridges
  - Hermes external skill directories and visible skills
  - cc-switch Claude provider skill listing budget
  - DBS route references
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --strict)
      strict=1
      ;;
    --lenient)
      strict=0
      ;;
    --verbose)
      verbose=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

ok() {
  echo "OK      $*"
}

detail() {
  if [ "$verbose" -eq 1 ]; then
    ok "$@"
  fi
}

warn() {
  echo "WARN    $*"
  if [ "$strict" -eq 1 ]; then
    status=1
  fi
}

fail() {
  echo "FAIL    $*"
  status=1
}

section() {
  echo
  echo "== $* =="
}

run_required_script() {
  local label="$1"
  shift

  section "$label"
  if "$@"; then
    ok "$label passed"
  else
    fail "$label failed"
  fi
}

expect_file_contains() {
  local file="$1"
  local pattern="$2"
  local label="$3"

  if [ ! -f "$file" ]; then
    fail "missing $label: $file"
  elif grep -Fq "$pattern" "$file"; then
    detail "$label contains $pattern"
  else
    fail "$label does not reference $pattern: $file"
  fi
}

check_openclaw_codex_bridge() {
  section "OpenClaw Codex skills"

  if [ ! -d "$HOME/.openclaw/acpx/codex-home" ]; then
    warn "OpenClaw Codex home not found; skipping OpenClaw bridge audit"
    return
  fi

  if [ ! -d "$openclaw_codex_skills" ]; then
    fail "missing OpenClaw Codex skills dir: $openclaw_codex_skills"
    return
  fi

  if [ -d "$openclaw_codex_skills/.system" ]; then
    ok "OpenClaw system skills preserved: $openclaw_codex_skills/.system"
  else
    warn "OpenClaw system skills dir not found under $openclaw_codex_skills"
  fi

  local checked=0
  while IFS= read -r skill_dir; do
    local name link target expected
    name="$(basename "$skill_dir")"
    link="$openclaw_codex_skills/$name"
    expected="$agents_skills/$name"

    if [ ! -e "$skill_dir/SKILL.md" ]; then
      continue
    fi

    if [ ! -e "$link" ] && [ ! -L "$link" ]; then
      fail "OpenClaw Codex missing bridge for $name"
      continue
    fi

    if [ ! -L "$link" ]; then
      fail "OpenClaw Codex has local non-symlink for shared skill: $link"
      continue
    fi

    target="$(readlink "$link")"
    if [ "$target" = "$expected" ]; then
      checked=$((checked + 1))
      detail "OpenClaw $name -> $expected"
    else
      fail "OpenClaw Codex bridge target mismatch for $name: $target, expected $expected"
    fi
  done < <(find "$source_dir" -mindepth 1 -maxdepth 1 -type d | sort)

  ok "OpenClaw Codex checked $checked shared skill bridges"
}

check_claude_commands() {
  section "Claude Code slash commands"

  if [ ! -d "$claude_commands" ]; then
    fail "missing Claude commands dir: $claude_commands"
    return
  fi

  local command checked=0
  while IFS= read -r skill_dir; do
    command="$(basename "$skill_dir")"
    expect_file_contains "$claude_commands/$command.md" "$source_dir/$command/SKILL.md" "Claude command /$command"
    checked=$((checked + 1))
  done < <(find "$source_dir" -mindepth 1 -maxdepth 1 -type d -name 'dbs*' | sort)

  expect_file_contains "$claude_commands/shuiqiupao-perspective.md" "$source_dir/shuiqiupao-perspective/SKILL.md" "Claude command /shuiqiupao-perspective"
  expect_file_contains "$claude_commands/水球泡.md" "$source_dir/shuiqiupao-perspective/SKILL.md" "Claude command /水球泡"
  expect_file_contains "$claude_commands/水汽炮.md" "$source_dir/shuiqiupao-perspective/SKILL.md" "Claude command /水汽炮"

  ok "Claude Code checked $checked DBS command bridges plus Shuiqiupao aliases"
}

check_hermes_profile() {
  local label="$1"
  local wrapper="$2"
  local config="$3"

  section "Hermes $label"

  if [ ! -x "$wrapper" ]; then
    warn "Hermes $label wrapper not executable: $wrapper"
    return
  fi

  expect_file_contains "$config" "$agents_skills" "Hermes $label config"

  local list_output
  if ! list_output="$(COLUMNS=240 "$wrapper" skills list --source local --enabled-only 2>/dev/null)"; then
    fail "Hermes $label skills list failed"
    return
  fi

  local skill checked=0
  while IFS= read -r skill; do
    if printf '%s\n' "$list_output" | grep -Fq "$skill"; then
      detail "Hermes $label sees $skill"
      checked=$((checked + 1))
    elif check_hermes_shadow_bridge "$label" "$skill" "creative"; then
      detail "Hermes $label has shadow bridge for $skill"
      checked=$((checked + 1))
    else
      fail "Hermes $label does not list $skill"
    fi
  done < <(
    find "$source_dir" -mindepth 1 -maxdepth 1 -type d \
      -exec test -f '{}/SKILL.md' ';' -print \
      | sed 's#^.*/##' \
      | sort
  )

  ok "Hermes $label sees $checked truth-source skills"
}

check_hermes_shadow_bridge() {
  local label="$1"
  local skill="$2"
  local category="$3"
  local path

  case "$skill" in
    humanizer|baoyu-comic|baoyu-infographic)
      ;;
    *)
      return 1
      ;;
  esac

  case "$label" in
    personal)
      path="$HOME/.hermes/profiles/personal/skills/$category/$skill"
      ;;
    automation)
      path="$HOME/.hermes/profiles/automation/skills/$category/$skill"
      ;;
    *)
      return 1
      ;;
  esac

  if [ ! -L "$path" ]; then
    return 1
  fi

  if [ "$(readlink "$path")" != "$agents_skills/$skill" ]; then
    return 1
  fi

  [ -f "$path/SKILL.md" ]
}

check_cc_switch() {
  section "cc-switch"

  local db="$HOME/.cc-switch/cc-switch.db"
  if [ ! -f "$db" ]; then
    warn "cc-switch db not found; skipping cc-switch audit"
    return
  fi

  if ! command -v sqlite3 >/dev/null 2>&1; then
    warn "sqlite3 not available; skipping cc-switch audit"
    return
  fi

  local rows bad
  rows="$(sqlite3 "$db" "select count(*) from providers where app_type='claude';")"
  if [ "${rows:-0}" -eq 0 ]; then
    warn "cc-switch has no Claude providers"
    return
  fi

  bad="$(
    sqlite3 "$db" \
      "select name || ' (' || id || ')' from providers where app_type='claude' and coalesce(json_extract(settings_config,'$.skillListingBudgetFraction'), '') != 0.05;"
  )"

  if [ -n "$bad" ]; then
    fail "cc-switch Claude providers missing skillListingBudgetFraction=0.05:"
    printf '%s\n' "$bad"
  else
    ok "cc-switch Claude providers have skillListingBudgetFraction=0.05"
  fi
}

echo "Repository: $repo_dir"
echo "Truth source: $source_dir"
echo "Shared alias: $agents_skills"

run_required_script "Claude/Codex bridge audit" "$repo_dir/scripts/audit-skill-bridges.sh"
run_required_script "DBS route audit" bash "$repo_dir/scripts/audit-skill-routes.sh"
check_openclaw_codex_bridge
check_claude_commands
check_hermes_profile "personal" "$HOME/.local/bin/hermes-personal" "$HOME/.hermes/profiles/personal/config.yaml"
check_hermes_profile "automation" "$HOME/.local/bin/hermes-automation" "$HOME/.hermes/profiles/automation/config.yaml"
check_cc_switch

echo
if [ "$status" -eq 0 ]; then
  echo "Agent skill host audit passed."
else
  echo "Agent skill host audit failed."
fi

exit "$status"
