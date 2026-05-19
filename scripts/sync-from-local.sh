#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
local_source="${1:-$HOME/.agents/skills}"

if [ ! -d "$local_source" ]; then
  echo "Missing local source: $local_source" >&2
  exit 1
fi

rsync -a --delete \
  --exclude '.git/' \
  --exclude '.DS_Store' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  "$local_source/" "$repo_dir/skills/"

echo "Synced $local_source -> $repo_dir/skills"

