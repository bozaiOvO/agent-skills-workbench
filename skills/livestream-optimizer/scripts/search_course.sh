#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 '<pattern>'" >&2
  exit 1
fi

COURSE_DIR="/Users/bo/Documents/2026/陈晶直播课程"
PATTERN="$1"

rg -n --glob '*.txt' "$PATTERN" "$COURSE_DIR"
