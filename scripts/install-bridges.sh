#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_dir/skills"
agents_dir="$HOME/.agents"
agents_skills="$agents_dir/skills"

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

link_host_skills() {
  local host_dir="$1"
  mkdir -p "$host_dir"
  find "$source_dir" -mindepth 1 -maxdepth 1 -type d | while IFS= read -r skill_dir; do
    local name
    name="$(basename "$skill_dir")"
    case "$name" in
      .*) continue ;;
    esac
    if [ -e "$skill_dir/SKILL.md" ] || [ -d "$skill_dir" ]; then
      if [ -e "$host_dir/$name" ] && [ ! -L "$host_dir/$name" ]; then
        echo "Skipping existing non-symlink: $host_dir/$name"
        continue
      fi
      ln -sfn "$agents_skills/$name" "$host_dir/$name"
    fi
  done
}

link_host_skills "$HOME/.codex/skills"
link_host_skills "$HOME/.claude/skills"

echo "Installed skill source and bridges:"
echo "  $agents_skills -> $source_dir"
echo "  $HOME/.codex/skills/* -> $agents_skills/*"
echo "  $HOME/.claude/skills/* -> $agents_skills/*"

