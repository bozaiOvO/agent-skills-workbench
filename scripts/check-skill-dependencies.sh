#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

count_files() {
  local path="$1"
  if [ -d "$path" ]; then
    find "$path" -type f ! -name '.DS_Store' | wc -l | tr -d ' '
  else
    echo "0"
  fi
}

show_dir() {
  local label="$1"
  local path="$2"
  if [ -d "$path" ]; then
    echo "OK      $label -> $path ($(count_files "$path") files)"
  else
    echo "MISSING $label -> $path"
  fi
}

show_file() {
  local label="$1"
  local path="$2"
  if [ -f "$path" ]; then
    echo "OK      $label -> $path"
  else
    echo "MISSING $label -> $path"
  fi
}

show_env_dir() {
  local label="$1"
  local var_name="$2"
  local fallback="$3"
  local raw="${!var_name:-}"
  local path="${raw:-$fallback}"
  local source="fallback"
  if [ -n "$raw" ]; then
    source="$var_name"
  fi
  if [ -d "$path" ]; then
    echo "OK      $label -> $path ($source, $(count_files "$path") files)"
  else
    echo "MISSING $label -> $path ($source)"
  fi
}

show_env_file() {
  local label="$1"
  local var_name="$2"
  local fallback="$3"
  local raw="${!var_name:-}"
  local path="${raw:-$fallback}"
  local source="fallback"
  if [ -n "$raw" ]; then
    source="$var_name"
  fi
  if [ -f "$path" ]; then
    echo "OK      $label -> $path ($source)"
  else
    echo "MISSING $label -> $path ($source)"
  fi
}

echo "Repository: $repo_dir"
echo
echo "Bundled corpus/data tracked with the repo:"
show_dir "kge-perspective corpus" "$repo_dir/skills/kge-perspective/assets/corpus"
show_dir "shuiqiupao corpus" "$repo_dir/skills/shuiqiupao-perspective/assets/corpus"
show_dir "shuiqiupao paopaoshuo" "$repo_dir/skills/shuiqiupao-perspective/assets/paopaoshuo"
show_dir "tianya board research" "$repo_dir/skills/tianya-perspective/references/research/boards"
show_dir "don-ge distilled references" "$repo_dir/skills/don-ge-skill/references"
show_dir "fengge distilled references" "$repo_dir/skills/fengge-perspective/references"
show_dir "programmer-luck distilled references" "$repo_dir/skills/程序员luck视角/references"
show_dir "livestream distilled references" "$repo_dir/skills/livestream-optimizer/references"

echo
echo "External corpus/runtime dependencies on this Mac:"
show_env_dir "don-ge raw refresh corpus" "DON_GE_CORPUS_DIR" "/Users/bo/Desktop/TikTokDownloader-master/Volume/整理输出_按年份热度/dontbesilent 聊赚钱"
show_env_dir "fengge raw dataset" "FENGGE_DATASET_ROOT" "/Users/bo/Desktop/TikTokDownloader-master/Volume/Zhoulifeng-Streaming-Dataset"
show_env_dir "programmer-luck raw corpus" "LUCK_CORPUS_DIR" "$HOME/Desktop/TikTokDownloader-master/Volume/整理输出_按年份热度/程序员luck"
show_env_dir "livestream course transcripts" "LIVESTREAM_COURSE_DIR" "/Users/bo/Documents/2026/陈晶直播课程"
show_env_file "qieman weeklies JSON" "QIEMAN_WEEKLIES_PATH" "/private/tmp/qieman_weeklies_2025_2026.json"
show_file "wechat daily config" "$HOME/.config/wechat-daily.json"
show_file "wechat keys" "$HOME/.config/wechat-keys.json"
if command -v wx >/dev/null 2>&1; then
  echo "OK      wx-cli binary -> $(command -v wx)"
else
  echo "MISSING wx-cli binary -> install @jackwener/wx-cli before using wx-cli"
fi
show_file "wx-cli config" "$HOME/.wx-cli/config.json"

echo
echo "Bridge:"
if [ -L "$HOME/.agents/skills" ]; then
  echo "OK      ~/.agents/skills -> $(readlink "$HOME/.agents/skills")"
else
  echo "MISSING ~/.agents/skills symlink"
fi
