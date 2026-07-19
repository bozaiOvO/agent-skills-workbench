#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_dir/skills"
agents_skills="$HOME/.agents/skills"
status=0
verbose=0

# Comma-separated local exceptions, for example:
#   ALLOW_LOCAL_SKILLS=wechat-screen-reader,videocut ./scripts/audit-skill-bridges.sh
default_allowed_local="wechat-screen-reader,videocut,videocut-cut,videocut-hd,videocut-install,videocut-subtitle,videocut-voice"
allowed_local=",${default_allowed_local},${ALLOW_LOCAL_SKILLS:-},"

usage() {
  cat <<'EOF'
Usage: audit-skill-bridges.sh [--verbose]

Verifies that shared user skills live in the repository truth source and appear
in Claude/Codex host directories only as symlinks.

Environment:
  ALLOW_LOCAL_SKILLS=name1,name2   Permit documented host-local exceptions.

Documented defaults:
  wechat-screen-reader
  videocut, videocut-cut, videocut-hd, videocut-install, videocut-subtitle, videocut-voice
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
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
  if [ "$verbose" -eq 1 ]; then
    echo "OK      $*"
  fi
}

warn() {
  echo "WARN    $*"
}

fail() {
  echo "FAIL    $*"
  status=1
}

is_allowed_local() {
  local name="$1"
  case "$name" in
    .DS_Store|.system)
      return 0
      ;;
  esac
  case "$allowed_local" in
    *,"$name",*)
      return 0
      ;;
  esac
  return 1
}

check_agents_bridge() {
  if [ ! -d "$source_dir" ]; then
    fail "missing source skills dir: $source_dir"
    return
  fi

  if [ ! -L "$agents_skills" ]; then
    fail "$agents_skills is not a symlink to $source_dir"
    return
  fi

  local target
  target="$(readlink "$agents_skills")"
  if [ "$target" = "$source_dir" ]; then
    ok "$agents_skills -> $source_dir"
  else
    fail "$agents_skills points to $target, expected $source_dir"
  fi
}

check_host_bridge() {
  local host_name="$1"
  local host_dir="$2"
  local checked=0

  echo
  echo "$host_name bridge: $host_dir"

  if [ ! -d "$host_dir" ]; then
    fail "missing host skill dir: $host_dir"
    return
  fi

  while IFS= read -r skill_dir; do
    local name expected link target
    name="$(basename "$skill_dir")"
    expected="$agents_skills/$name"
    link="$host_dir/$name"

    if [ ! -e "$skill_dir/SKILL.md" ]; then
      continue
    fi

    if [ ! -e "$link" ] && [ ! -L "$link" ]; then
      fail "$host_name missing bridge for $name"
    elif [ ! -L "$link" ]; then
      fail "$host_name has local non-symlink for shared skill: $link"
    else
      target="$(readlink "$link")"
      if [ "$target" = "$expected" ]; then
        ok "$name -> $expected"
        checked=$((checked + 1))
      else
        fail "$host_name bridge target mismatch for $name: $target, expected $expected"
      fi
    fi
  done < <(find "$source_dir" -mindepth 1 -maxdepth 1 -type d | sort)

  while IFS= read -r entry; do
    local name
    name="$(basename "$entry")"

    if is_allowed_local "$name"; then
      continue
    fi

    if [ -L "$entry" ]; then
      if [ ! -e "$entry" ]; then
        fail "$host_name has broken symlink: $entry -> $(readlink "$entry")"
      fi
      continue
    fi

    if [ -f "$entry/SKILL.md" ]; then
      fail "$host_name has unmanaged local skill outside truth source: $entry"
    else
      warn "$host_name has extra local entry: $entry"
    fi
  done < <(find "$host_dir" -mindepth 1 -maxdepth 1 -print | sort)

  echo "Checked $checked shared skill bridges for $host_name."
}

echo "Repository: $repo_dir"
echo "Truth source: $source_dir"
echo

check_agents_bridge
check_host_bridge "Codex" "$HOME/.codex/skills"
check_host_bridge "Claude" "$HOME/.claude/skills"

echo
if [ "$status" -eq 0 ]; then
  echo "Skill bridge audit passed."
else
  echo "Skill bridge audit failed."
  echo "Shared user skills should live in $source_dir and appear in host dirs only as symlinks."
fi

exit "$status"
