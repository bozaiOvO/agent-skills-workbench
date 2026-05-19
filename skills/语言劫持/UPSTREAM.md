# 上游来源

- **仓库**：https://github.com/yiyi13769-cmd/language-hijack-playbook
- **默认分支**：master
- **首次拉取日期**：2026-05-09
- **拉取方式**：`curl` 逐字克隆 raw 文件，未做任何重写、提炼或软化

## 同步策略

**手动同步，不自动追上游**。理由：
1. 上游可能改写、删减或被 GitHub 下架，本地版本是确定的快照
2. 本 skill 已基于当时内容写好 SKILL.md 路由，自动同步可能破坏路由

## 重新同步命令

```bash
cd ~/.agents/skills/语言劫持
curl -s -o README.md            https://raw.githubusercontent.com/yiyi13769-cmd/language-hijack-playbook/master/README.md
curl -s -o playbooks/sun-yuchen.md   https://raw.githubusercontent.com/yiyi13769-cmd/language-hijack-playbook/master/playbooks/sun-yuchen.md
curl -s -o playbooks/mimeng.md       https://raw.githubusercontent.com/yiyi13769-cmd/language-hijack-playbook/master/playbooks/mimeng.md
curl -s -o playbooks/hybrid-guide.md https://raw.githubusercontent.com/yiyi13769-cmd/language-hijack-playbook/master/playbooks/hybrid-guide.md
curl -s -o tools/checklist.md   https://raw.githubusercontent.com/yiyi13769-cmd/language-hijack-playbook/master/tools/checklist.md
curl -s -o tools/templates.md   https://raw.githubusercontent.com/yiyi13769-cmd/language-hijack-playbook/master/tools/templates.md
```

## 字节数快照（首次拉取时）

| 文件 | 字节数 |
|---|---|
| README.md | 3272 |
| playbooks/sun-yuchen.md | 7220 |
| playbooks/mimeng.md | 7699 |
| playbooks/hybrid-guide.md | 4374 |
| tools/checklist.md | 2866 |
| tools/templates.md | 4805 |
| **合计** | **30236** |

如果 `wc -c` 结果与上表一致，说明文件未被改动。
