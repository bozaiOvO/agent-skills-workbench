#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skills_dir="$repo_dir/skills"
status=0

fail() {
  echo "FAIL    $*"
  status=1
}

ok() {
  echo "OK      $*"
}

if [ ! -d "$skills_dir" ]; then
  fail "missing skills dir: $skills_dir"
  exit "$status"
fi

echo "Skill route audit:"

found=0
while IFS= read -r ref; do
  found=$((found + 1))
  if [ -f "$skills_dir/$ref/SKILL.md" ]; then
    ok "/$ref -> skills/$ref/SKILL.md"
  else
    fail "DBS route points to missing skill: /$ref"
  fi
done < <(
  rg -No '`/dbs-[A-Za-z0-9_-]+`' "$skills_dir"/dbs*/SKILL.md \
    | sed -E 's/^.*`\/([^`]+)`$/\1/' \
    | sort -u
)

if [ "$found" -eq 0 ]; then
  ok "no DBS slash routes found"
fi

if [ "$status" -eq 0 ]; then
  echo "Skill route audit passed."
else
  echo "Skill route audit failed."
  echo "Every /dbs-* route referenced by DBS skills must have skills/<name>/SKILL.md."
fi

exit "$status"
