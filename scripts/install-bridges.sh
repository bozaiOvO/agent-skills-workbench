#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_dir/skills"
agents_dir="$HOME/.agents"
agents_skills="$agents_dir/skills"
openclaw_codex_skills="$HOME/.openclaw/acpx/codex-home/skills"
strict=1

usage() {
  cat <<'EOF'
Usage: install-bridges.sh [--strict|--lenient]

Creates skill symlink bridges:
  ~/.agents/skills -> repo skills/
  ~/.codex/skills/<skill> -> ~/.agents/skills/<skill>
  ~/.claude/skills/<skill> -> ~/.agents/skills/<skill>
  ~/.openclaw/acpx/codex-home/skills/<skill> -> ~/.agents/skills/<skill>
    when OpenClaw's Codex HOME exists

Default: --strict. After installing, audit all known local agent hosts and fail
on unmanaged drift.
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

if [ ! -d "$source_dir" ]; then
  echo "Missing skills source: $source_dir" >&2
  exit 1
fi

mkdir -p "$agents_dir" "$HOME/.codex/skills" "$HOME/.claude/skills"

if [ -e "$agents_skills" ] && [ ! -L "$agents_skills" ]; then
  backup="$agents_skills.backup-$(date +%Y%m%d-%H%M%S)"
  echo "Backing up existing $agents_skills to $backup"
  mv "$agents_skills" "$backup"
fi

ln -sfn "$source_dir" "$agents_skills"

clean_broken_links() {
  local host_dir="$1"
  find "$host_dir" -maxdepth 1 -type l -print0 | while IFS= read -r -d '' link; do
    if [ ! -e "$link" ]; then
      echo "Removing broken symlink: $link -> $(readlink "$link")"
      rm "$link"
    fi
  done
}

link_host_skills() {
  local host_dir="$1"
  mkdir -p "$host_dir"
  clean_broken_links "$host_dir"

  find "$source_dir" -mindepth 1 -maxdepth 1 -type d | while IFS= read -r skill_dir; do
    local name
    name="$(basename "$skill_dir")"
    case "$name" in
      .*) continue ;;
    esac
    if [ -e "$skill_dir/SKILL.md" ] || [ -d "$skill_dir" ]; then
      if [ -e "$host_dir/$name" ] && [ ! -L "$host_dir/$name" ]; then
        echo "Conflict: existing non-symlink blocks bridge: $host_dir/$name" >&2
        continue
      fi
      ln -sfn "$agents_skills/$name" "$host_dir/$name"
    fi
  done
}

ensure_hermes_external_dir() {
  local config="$1"
  local label="$2"

  if [ ! -f "$config" ]; then
    return
  fi

  if grep -Fq "$agents_skills" "$config"; then
    echo "Hermes $label already loads $agents_skills"
    return
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 not found; cannot update Hermes $label config: $config" >&2
    return
  fi

  local backup
  backup="$config.backup-$(date +%Y%m%d-%H%M%S)"
  cp "$config" "$backup"

  python3 - "$config" "$agents_skills" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
skill_dir = sys.argv[2]
text = path.read_text()
lines = text.splitlines()

def indent_of(line):
    return len(line) - len(line.lstrip(" "))

skills_i = next((i for i, line in enumerate(lines) if re.match(r"^skills:\s*$", line)), None)

if skills_i is None:
    if lines and lines[-1].strip():
        lines.append("")
    lines.extend(["skills:", "  external_dirs:", f"    - {skill_dir}"])
else:
    end = len(lines)
    for j in range(skills_i + 1, len(lines)):
        stripped = lines[j].strip()
        if stripped and not lines[j].startswith((" ", "\t")) and not stripped.startswith("#"):
            end = j
            break

    ext_i = None
    for j in range(skills_i + 1, end):
        if re.match(r"^\s+external_dirs\s*:", lines[j]):
            ext_i = j
            break

    if ext_i is None:
        lines.insert(skills_i + 1, "  external_dirs:")
        lines.insert(skills_i + 2, f"    - {skill_dir}")
    else:
        prefix, rest = lines[ext_i].split(":", 1)
        ext_indent = indent_of(lines[ext_i])
        rest = rest.strip()

        insert = ext_i + 1
        item_indent = ext_indent + 2

        if rest == "[]":
            lines[ext_i] = f"{prefix}:"
        elif rest.startswith("[") and rest.endswith("]"):
            entries = [item.strip().strip("'\"") for item in rest[1:-1].split(",") if item.strip()]
            lines[ext_i] = f"{prefix}:"
            for entry in entries:
                lines.insert(insert, " " * item_indent + f"- {entry}")
                insert += 1
                end += 1

        for j in range(ext_i + 1, end):
            stripped = lines[j].strip()
            if not stripped:
                continue
            if stripped.startswith("- "):
                item_indent = indent_of(lines[j])
                break
            if indent_of(lines[j]) <= ext_indent:
                break

        insert = ext_i + 1
        while insert < end:
            stripped = lines[insert].strip()
            if not stripped:
                insert += 1
                continue
            if indent_of(lines[insert]) <= ext_indent and not stripped.startswith("- "):
                break
            if stripped.startswith("- ") and indent_of(lines[insert]) != item_indent:
                break
            insert += 1

        lines.insert(insert, " " * item_indent + f"- {skill_dir}")

path.write_text("\n".join(lines) + "\n")
PY

  echo "Updated Hermes $label config: $config (backup: $backup)"
}

repair_cc_switch_skill_budget() {
  local db="$HOME/.cc-switch/cc-switch.db"

  if [ ! -f "$db" ]; then
    return
  fi

  if ! command -v sqlite3 >/dev/null 2>&1; then
    echo "sqlite3 not found; cannot update cc-switch provider settings" >&2
    return
  fi

  local bad_count
  bad_count="$(
    sqlite3 "$db" \
      "select count(*) from providers where app_type='claude' and (json_valid(settings_config)=0 or coalesce(case when json_valid(settings_config) then json_extract(settings_config,'$.skillListingBudgetFraction') end, '') != 0.05);"
  )"

  if [ "${bad_count:-0}" -eq 0 ]; then
    echo "cc-switch Claude providers already have skillListingBudgetFraction=0.05"
    return
  fi

  local backup
  backup="$db.backup-$(date +%Y%m%d-%H%M%S)"
  cp "$db" "$backup"

  sqlite3 "$db" \
    "update providers set settings_config=json_set(case when json_valid(settings_config) then settings_config else '{}' end, '$.skillListingBudgetFraction', 0.05) where app_type='claude' and (json_valid(settings_config)=0 or coalesce(case when json_valid(settings_config) then json_extract(settings_config,'$.skillListingBudgetFraction') end, '') != 0.05);"

  echo "Updated $bad_count cc-switch Claude provider(s) (backup: $backup)"
}

bridge_hermes_shadowed_skill() {
  local skill_name="$1"
  local category="$2"
  local target="$agents_skills/$skill_name"

  if [ ! -d "$target" ]; then
    return
  fi

  local path parent backup
  for path in \
    "$HOME/.hermes/skills/$category/$skill_name" \
    "$HOME/.hermes/profiles/personal/skills/$category/$skill_name" \
    "$HOME/.hermes/profiles/automation/skills/$category/$skill_name"
  do
    parent="$(dirname "$path")"
    if [ ! -d "$parent" ]; then
      continue
    fi

    if [ -L "$path" ]; then
      if [ "$(readlink "$path")" = "$target" ]; then
        echo "Hermes shadowed skill already bridged: $path -> $target"
        continue
      fi
      rm "$path"
    elif [ -e "$path" ]; then
      backup="$path.backup-$(date +%Y%m%d-%H%M%S)"
      mv "$path" "$backup"
      echo "Backed up Hermes shadowed skill: $path -> $backup"
    fi

    ln -sfn "$target" "$path"
    echo "Bridged Hermes shadowed skill: $path -> $target"
  done
}

link_host_skills "$HOME/.codex/skills"
link_host_skills "$HOME/.claude/skills"
if [ -d "$(dirname "$openclaw_codex_skills")" ]; then
  link_host_skills "$openclaw_codex_skills"
fi

ensure_hermes_external_dir "$HOME/.hermes/profiles/personal/config.yaml" "personal"
ensure_hermes_external_dir "$HOME/.hermes/profiles/automation/config.yaml" "automation"
bridge_hermes_shadowed_skill "humanizer" "creative"
bridge_hermes_shadowed_skill "baoyu-comic" "creative"
bridge_hermes_shadowed_skill "baoyu-infographic" "creative"
repair_cc_switch_skill_budget

echo "Installed skill source and bridges:"
echo "  $agents_skills -> $source_dir"
echo "  $HOME/.codex/skills/* -> $agents_skills/*"
echo "  $HOME/.claude/skills/* -> $agents_skills/*"
if [ -d "$openclaw_codex_skills" ]; then
  echo "  $openclaw_codex_skills/* -> $agents_skills/*"
fi

warn_running_claude_sessions() {
  local running
  running="$(
    ps -axo pid=,lstart=,command= \
      | awk '$0 ~ /(^|[[:space:]])[Cc]laude([[:space:]]|$)/ && $0 !~ /install-bridges/ { print "  " $0 }'
  )"

  if [ -n "$running" ]; then
    echo
    echo "Notice: running Claude/Claude Code sessions may keep an old skill list:"
    echo "$running"
    echo "Restart those sessions after bridge changes so skills are reloaded."
  fi
}

echo
bash "$repo_dir/scripts/install-claude-commands.sh"

if [ "$strict" -eq 1 ]; then
  echo
  "$repo_dir/scripts/audit-agent-skill-hosts.sh" --strict
else
  echo
  echo "Lenient mode: audit warnings are informational."
  "$repo_dir/scripts/audit-agent-skill-hosts.sh" --lenient || true
fi

warn_running_claude_sessions
