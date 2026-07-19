# Skill Sync Notes

This repository is intended to be the GitHub-backed source for shared local agent skills.
The short contract lives in [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md).

## Source Of Truth Contract

There are three layers:

- GitHub remote: `git@github.com:bozaiOvO/agent-skills-workbench.git`
- Local repo source: whatever path on this Mac contains this repository
- Agent bridges:
  - `~/.agents/skills` -> `<local-repo>/skills`
  - `~/.codex/skills/*` -> `~/.agents/skills/*`
  - `~/.claude/skills/*` -> `~/.agents/skills/*`
  - `~/.openclaw/acpx/codex-home/skills/*` -> `~/.agents/skills/*` when OpenClaw is installed
  - Hermes profiles load `~/.agents/skills` via `skills.external_dirs`

Do not copy skills into each agent one by one. Use symlinks so one local repo update reaches every agent on that Mac.

Host directories are bridge layers, not maintenance layers:

- OK: Codex/Claude platform or bundled skills that are owned by the host.
- OK: `~/.claude/skills/<name>` and `~/.codex/skills/<name>` symlink to `~/.agents/skills/<name>`.
- Not OK: user-maintained functional skills living as real directories under `~/.claude/skills` or `~/.codex/skills`.

Run this after installs, pulls, or skill creation:

```bash
bash scripts/audit-skill-bridges.sh
bash scripts/audit-skill-routes.sh
bash scripts/install-claude-commands.sh
bash scripts/audit-agent-skill-hosts.sh
```

`scripts/install-bridges.sh` runs the all-host audit in strict mode by default and regenerates Claude Code command bridges. If the audit fails, do not keep patching one host by hand; either promote the local skill into `skills/` or explicitly document it as a host-only exception.

The installer also repairs Hermes profile `skills.external_dirs` and cc-switch Claude provider `skillListingBudgetFraction` when those configs exist locally.

OpenClaw is a special case: its Codex wrapper sets `CODEX_HOME` to `~/.openclaw/acpx/codex-home`, so it does not automatically see `~/.codex/skills`. Keep its `skills/.system` directory intact and add only per-skill symlinks into `~/.openclaw/acpx/codex-home/skills`.

Hermes has another special case: local/builtin skills are scanned before external dirs. If a truth-source skill name is shadowed by a Hermes local copy, bridge the local Hermes entry back to `~/.agents/skills/<name>` with a backup. Current known shadow: `creative/humanizer`.

## Find The Existing Local Source First

Do not assume the repo lives under `~/Documents`. On a target Mac, first inspect the existing source:

```bash
readlink ~/.agents/skills
```

If that points to a `skills/` directory, inspect the parent repository:

```bash
repo_dir="$(cd "$(readlink ~/.agents/skills)/.." && pwd)"
git -C "$repo_dir" remote -v
git -C "$repo_dir" status --short
```

If the remote is this repository, use that path as the local source of truth. Only clone a new copy when no existing source can be found, and choose the clone path explicitly instead of defaulting to `~/Documents`.

After the repo path is known:

```bash
git -C "$repo_dir" pull --ff-only origin main
bash "$repo_dir/scripts/install-bridges.sh"
bash "$repo_dir/scripts/audit-skill-routes.sh"
bash "$repo_dir/scripts/check-skill-dependencies.sh"
```

## Local-Only Skills

The following skills are intentionally not synced to GitHub. They may exist on the main Mac, but should not be uploaded or auto-installed on other machines:

- `huashu-nuwa`
- `douyin-hot-pipeline`
- `zhangxuefeng-perspective`
- `小K视角`
- `silent-middleaged`
- `learning-lobster`
- `codex-primary-runtime`

Reasons include local corpus dependency, machine-specific scripts, experimental workflow status, or user preference.

## Dependency Rule

The skill `description` tells an agent when to trigger a skill. It is not enough to prove the skill is fully operational. Corpus and runtime dependencies are tracked in [SKILL_DEPENDENCIES.md](SKILL_DEPENDENCIES.md) and in the dependency notes inside the high-risk skill files.

Short version:

- Bundled corpus in GitHub: `kge-perspective`, `shuiqiupao-perspective`, `tianya-perspective`
- Bundled distilled references, but raw corpus external or optional: `don-ge-skill`, `fengge-perspective`, `程序员luck视角`, `livestream-optimizer`
- Runtime/login/local-app dependent: `qieman-weekly-links`, `wechat-daily`, `wx-cli`, `agent-browser`

`qieman-weekly-links` and `agent-browser` are intentionally synced. Their code/instructions should be shared across Macs, but Feishu login state, Chrome/CDP sessions, browser cookies, and `/private/tmp` extraction files stay machine-local.

`qieman-weekly-links` also includes a portable generated snapshot:

- `skills/qieman-weekly-links/assets/且曼周刊推荐内容链接汇总.md`

If a corpus is not in GitHub, prefer a machine-local data source such as `~/.agents/data/<skill-name>/...`, then point the skill to it with the documented environment variable. Do not commit private or large source corpora unless the user explicitly decides to make that corpus part of the remote source.

## Prompt For Mac Mini Sync

Use this prompt on the Mac mini:

```text
请把这台 Mac mini 的 agent skills 整理成“GitHub 远程真源 + 本机仓库真源 + 多 agent 软链接桥接”的结构。

远程仓库：
https://github.com/bozaiOvO/agent-skills-workbench

要求：
1. 先检查现有真源，不要假设仓库在 ~/Documents。先执行 readlink ~/.agents/skills；如果它指向某个 skills 目录，就把父目录当候选仓库，检查 git remote -v 和 git status --short。
2. 如果候选仓库 remote 是 bozaiOvO/agent-skills-workbench，就使用这个现有路径，不要重复 clone。
3. 如果没有现有仓库，再问我要 clone 到哪个路径；不要自行默认放到 Documents。
4. 对现有仓库先 git status --short。若有未提交改动，不要覆盖，先报告。工作区干净后 git pull --ff-only origin main。
5. 跑 bash scripts/install-bridges.sh，让 ~/.agents/skills 指向仓库 skills，并让 ~/.codex/skills 与 ~/.claude/skills 指向 ~/.agents/skills。
6. 如果发现 ~/.codex/skills 或 ~/.claude/skills 里已有同名 skill 且不是软链接，不要删除，不要合并，先列出冲突让我确认。
7. 不要自行恢复这些本地专用 skill：huashu-nuwa、douyin-hot-pipeline、zhangxuefeng-perspective、小K视角、silent-middleaged、learning-lobster。
8. qieman-weekly-links 和 agent-browser 要同步过去。注意：同步的是 skill、脚本和 assets/且曼周刊推荐内容链接汇总.md；不同步飞书登录态、Chrome/CDP 会话、浏览器 cookies、/private/tmp 原始 JSON。
9. Mac mini 上如果只需要读且曼周刊现成汇总，直接看仓库里的 skills/qieman-weekly-links/assets/且曼周刊推荐内容链接汇总.md。
10. Mac mini 上如果要重新提取且曼周刊：先保证 Feishu 在 Chrome 里已登录，再开启可调试 Chrome/CDP（默认端口 9223），用 curl -s http://127.0.0.1:9223/json/list 验证；然后按 qieman-weekly-links/SKILL.md 设置 QIEMAN_WEEKLIES_PATH、QIEMAN_OUTPUT_MD、QIEMAN_OUTPUT_JSON，运行 scripts/extract_feishu_weekly_recommendation_links.mjs。
11. agent-browser 是浏览器自动化辅助工具；如果 Mac mini 没装 CLI，先执行 npm i -g agent-browser && agent-browser install。需要浏览器交互、登录态检查、页面点击/截图/提取时优先用它；但登录态仍然要在 Mac mini 本机完成。
12. 跑 bash scripts/check-skill-dependencies.sh，并按 SKILL_DEPENDENCIES.md 报告哪些语料随 GitHub 已存在，哪些需要本机外部路径、环境变量、浏览器登录态或微信本地数据库。
13. 最后报告仓库路径、commit hash、桥接结果、冲突目录、依赖检查结果。
```
