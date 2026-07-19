#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skills_dir="$repo_dir/skills"
commands_dir="$HOME/.claude/commands"

mkdir -p "$commands_dir"

write_skill_command() {
  local command_name="$1"
  local skill_name="$2"
  local description="$3"
  local skill_file="$skills_dir/$skill_name/SKILL.md"
  local command_file="$commands_dir/$command_name.md"

  if [ ! -f "$skill_file" ]; then
    echo "Missing skill for command /$command_name: $skill_file" >&2
    return 1
  fi

  cat > "$command_file" <<EOF
---
description: $description
argument-hint: "[input]"
---

Use the local skill at:

\`$skill_file\`

User input:

\`\$ARGUMENTS\`

Instructions:

1. Read the skill file above before answering.
2. Follow that skill's workflow exactly.
3. If the skill routes to another local skill, read that routed skill's \`SKILL.md\` from \`$skills_dir\` and continue there.
4. Do not merely summarize the skill. Execute the requested workflow.
EOF
}

write_shuiqiupao_command() {
  local command_name="$1"
  local skill_file="$skills_dir/shuiqiupao-perspective/SKILL.md"
  local command_file="$commands_dir/$command_name.md"

  if [ ! -f "$skill_file" ]; then
    echo "Missing skill for command /$command_name: $skill_file" >&2
    return 1
  fi

  cat > "$command_file" <<EOF
---
description: 水球泡视角。分析求职、职场、创业、社会规则、人性、关系、阶层流动、宏观变化和 AI 时代机会/风险。
argument-hint: "[问题]"
allowed-tools: Bash(python3 *)
---

Use the local 水球泡 skill at:

\`$skill_file\`

User input:

\`\$ARGUMENTS\`

Instructions:

1. Read the skill file above before answering.
2. Follow the skill's retrieval-first workflow.
3. When retrieval is needed, use the absolute command documented in the skill:
   \`python3 "\$HOME/.agents/skills/shuiqiupao-perspective/scripts/search_corpus.py" "<query>"\`
4. Answer in the skill's required voice and structure. Do not give a generic assistant answer.
EOF
}

write_skill_command "dbs" "dbs" "DBS / dontbesilent 商业工具箱入口。"
write_skill_command "dbs-action" "dbs-action" "DBS 执行力诊断。"
write_skill_command "dbs-agent-migration" "dbs-agent-migration" "DBS Agent 工作台迁移和 Claude/Codex skill bridge 整理。"
write_skill_command "dbs-ai-check" "dbs-ai-check" "DBS AI 写作特征识别。"
write_skill_command "dbs-benchmark" "dbs-benchmark" "DBS 对标分析。"
write_skill_command "dbs-chatroom" "dbs-chatroom" "DBS 定向聊天室。"
write_skill_command "dbs-chatroom-austrian" "dbs-chatroom-austrian" "DBS 奥派聊天室。"
write_skill_command "dbs-content" "dbs-content" "DBS 内容创作诊断。"
write_skill_command "dbs-content-system" "dbs-content-system" "DBS 内容资产结构化系统。"
write_skill_command "dbs-decision" "dbs-decision" "DBS 长期决策系统。"
write_skill_command "dbs-deconstruct" "dbs-deconstruct" "DBS 概念拆解。"
write_skill_command "dbs-diagnosis" "dbs-diagnosis" "DBS 商业模式问诊。"
write_skill_command "dbs-goal" "dbs-goal" "DBS 目标清晰化。"
write_skill_command "dbs-good-question" "dbs-good-question" "DBS 好问题生成器。"
write_skill_command "dbs-hook" "dbs-hook" "DBS 短视频开头优化。"
write_skill_command "dbs-learning" "dbs-learning" "DBS 交互式学习入口。"
write_skill_command "dbs-report" "dbs-report" "DBS 报告整理。"
write_skill_command "dbs-resonate" "dbs-resonate" "DBS 文稿共鸣诊断。"
write_skill_command "dbs-restore" "dbs-restore" "DBS 诊断状态恢复。"
write_skill_command "dbs-save" "dbs-save" "DBS 诊断状态保存。"
write_skill_command "dbs-slowisfast" "dbs-slowisfast" "DBS 慢就是快。"
write_skill_command "dbs-spread" "dbs-spread" "DBS 传播心理解码。"
write_skill_command "dbs-xhs-title" "dbs-xhs-title" "DBS 小红书标题公式。"
write_skill_command "dbskill-upgrade" "dbskill-upgrade" "DBSkill 全局安装升级。"
write_skill_command "zhangxuefeng-perspective" "zhangxuefeng-perspective" "张雪峰视角。分析教育选择、职业规划、阶层流动等问题。"
write_skill_command "张雪峰" "zhangxuefeng-perspective" "张雪峰视角。分析教育选择、职业规划、阶层流动等问题。"

write_shuiqiupao_command "shuiqiupao-perspective"
write_shuiqiupao_command "水球泡"
write_shuiqiupao_command "水汽炮"

echo "Installed Claude slash command bridges in $commands_dir"
