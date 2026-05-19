---
name: dbskill-upgrade
description: 升级全局安装的 dbskill 到最新版本，兼容 Codex 的 `$CODEX_HOME/skills` / `~/.codex/skills`。先检测安装目录、比对远程版本、创建备份、征得用户确认，再安全同步新版本；失败时从备份恢复。
trigger: /dbskill-upgrade、/升级dbskill、「升级 dbskill」
---

# dbskill-upgrade

把当前机器里全局安装的 dbskill 升到最新版。默认目标是 `${CODEX_HOME:-$HOME/.codex}/skills`，不是旧的 `~/.claude/skills`。

## 使用场景

- 用户主动要求升级已安装的 dbskill。
- 用户想先看本地版本、远程版本，再决定是否升级。
- 用户升级后还想知道替换了哪些 skill、备份放在哪、是否需要重启 Codex。

## 升级前检查点

在真正替换任何文件之前，先完成 4 件事：

1. 确认安装根目录。
2. 获取远程版本号；本地版本如果没有显式版本文件，就诚实显示 `unknown`。
3. 明确告诉用户会覆盖哪些 dbskill 目录，但会先备份。
4. 征得一次明确确认，再开始网络下载和全局写入。

如果用户只说“看看有没有更新”，那就只做版本检查，不做替换。

## 升级流程

### Step 1: 检测安装位置

```bash
CODEX_ROOT="${CODEX_HOME:-$HOME/.codex}"
INSTALL_DIR="$CODEX_ROOT/skills"

if [ ! -d "$INSTALL_DIR/dbs" ]; then
  echo "ERROR: dbskill not found in $INSTALL_DIR"
  exit 1
fi

echo "Install location: $INSTALL_DIR"
```

### Step 2: 获取当前版本

```bash
OLD_VERSION="unknown"
for candidate in \
  "$INSTALL_DIR/.dbskill-version" \
  "$INSTALL_DIR/dbskill-upgrade/VERSION"
do
  if [ -f "$candidate" ]; then
    OLD_VERSION=$(cat "$candidate")
    break
  fi
done

echo "Current installed version: $OLD_VERSION"
```

如果本地没有版本文件，不要编造版本号，直接显示 `unknown`。

### Step 3: 获取远程版本

```bash
REMOTE_VERSION=$(curl -fsSL https://raw.githubusercontent.com/dontbesilent2025/dbskill/main/VERSION)
if [ -z "$REMOTE_VERSION" ]; then
  echo "ERROR: Cannot fetch remote version"
  exit 1
fi

echo "Remote version: $REMOTE_VERSION"
```

### Step 4: 展示升级计划并征得确认

先告诉用户：

- 安装位置：`$INSTALL_DIR`
- 当前版本：`$OLD_VERSION`
- 远程版本：`$REMOTE_VERSION`
- 即将覆盖：`chatroom-austrian`、`dbs`、`dbs-*`、`dbskill-upgrade`
- 会先创建备份，失败可恢复

如果 `OLD_VERSION` 已知且等于 `REMOTE_VERSION`，直接告诉用户已是最新版本并结束。

如果用户没有明确同意，不进入后续步骤。

### Step 5: 下载远程仓库并解析待同步目录

```bash
TMP_DIR=$(mktemp -d)
REPO_DIR="$TMP_DIR/dbskill"

git clone --depth 1 https://github.com/dontbesilent2025/dbskill.git "$REPO_DIR"
if [ $? -ne 0 ]; then
  echo "ERROR: Failed to clone repository"
  rm -rf "$TMP_DIR"
  exit 1
fi

mapfile -t SKILL_DIRS < <(
  find "$REPO_DIR/skills" -mindepth 1 -maxdepth 1 -type d \
    \( -name 'chatroom-austrian' -o -name 'dbs' -o -name 'dbs-*' -o -name 'dbskill-upgrade' \) \
    | sort
)

if [ ${#SKILL_DIRS[@]} -eq 0 ]; then
  echo "ERROR: No dbskill directories found in remote repo"
  rm -rf "$TMP_DIR"
  exit 1
fi
```

### Step 6: 备份当前已安装目录

```bash
BACKUP_DIR="$INSTALL_DIR/.dbskill-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

for src in "${SKILL_DIRS[@]}"; do
  name=$(basename "$src")
  if [ -d "$INSTALL_DIR/$name" ]; then
    rsync -a "$INSTALL_DIR/$name/" "$BACKUP_DIR/$name/"
  fi
done

echo "Backup created: $BACKUP_DIR"
```

### Step 7: 安全同步新版本

不要用通配符 `rm -rf "$HOME/.claude/skills"/dbs*` 这类危险替换方式。改为逐目录校验后同步：

```bash
for src in "${SKILL_DIRS[@]}"; do
  name=$(basename "$src")
  if [ ! -f "$src/SKILL.md" ]; then
    echo "ERROR: Missing SKILL.md in $src"
    exit 1
  fi

  mkdir -p "$INSTALL_DIR/$name"
  rsync -a --delete "$src/" "$INSTALL_DIR/$name/"
done
```

这样只会覆盖目标 skill 目录，不会误删不相关的全局 skill。

### Step 8: 失败时恢复备份

如果下载、校验、同步任一步失败，按目录恢复：

```bash
for backup in "$BACKUP_DIR"/*; do
  [ -d "$backup" ] || continue
  name=$(basename "$backup")
  mkdir -p "$INSTALL_DIR/$name"
  rsync -a --delete "$backup/" "$INSTALL_DIR/$name/"
done

echo "Restored from backup: $BACKUP_DIR"
```

如果连备份都不存在，就明确告诉用户“未完成升级，也没有改动任何已安装目录”。

### Step 9: 展示升级结果

输出里至少要包含：

- 安装位置
- 本地版本与远程版本
- 实际同步了哪些 skill
- 备份目录
- 是否需要重启 Codex

如果仓库里没有结构化 changelog，就直接说：

```text
未找到结构化更新日志，已完成版本同步。
```

不要再保留这种占位文本：

```text
- [从 README 提取的更新要点]
```

### Step 10: 清理临时目录，保留备份

```bash
rm -rf "$TMP_DIR"
echo "Temporary files cleaned"
echo "Backup kept at: $BACKUP_DIR"
```

默认保留备份，不自动删。要删备份时，再单独征得用户同意。

## 输出格式

```text
dbskill 升级结果

- 安装位置：...
- 当前版本：...
- 远程版本：...
- 同步技能：...
- 备份目录：...
- 更新摘要：...

下一步：重启 Codex 以加载新的 skill。
```

## 错误处理

- 网络失败：说明是远程获取失败，不做替换。
- `git clone` 失败：说明仓库下载失败，不做替换。
- 远程仓库缺少 `skills/` 或 `SKILL.md`：停止升级并保留现状。
- 任一 `rsync` 失败：立即从备份恢复。
- 本地版本未知：允许升级，但要在结果里写明 `Current installed version: unknown`。

## 注意事项

- 默认只处理 dbskill 自己的 skill 目录，不动其他全局 skill。
- 升级动作涉及网络和全局写入，执行前要申请权限并征得用户确认。
- 升级完成后提醒用户重启 Codex。
