# 上游来源

- 仓库：https://github.com/kangarooking/cangjie-skill
- 默认分支：`main`
- 安装提交：`ead9e9ddc4bd8477f38573a6614ce8155e1aa505`
- 安装日期：2026-07-16
- 安装方式：从 GitHub 提交快照下载到本机 Agent Skills 真源

## 本机真源

`/Users/jinbo/Documents/agent-workbench/agent-skills-workbench/skills/cangjie-skill`

Codex、Claude Code、OpenClaw 等宿主只保留指向 `~/.agents/skills/cangjie-skill` 的桥接，不维护独立副本。

## 更新策略

手动审计后更新，不自动跟随上游。更新时先检查 `SKILL.md`、脚本、工作流和新增二进制文件，再替换真源快照并重跑 `scripts/install-bridges.sh --strict`。
