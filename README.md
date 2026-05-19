# Agent Skills Workbench

This repository is the source of truth for shared local agent skills.

## Layout

- `skills/`: human-maintained skill source.
- `scripts/install-bridges.sh`: creates symlink bridges for local agent hosts.
- `scripts/sync-from-local.sh`: updates this repository from `~/.agents/skills` on the main Mac.

## Install on a New Mac

Clone this repository, then run:

```bash
./scripts/install-bridges.sh
```

The script links:

- `~/.agents/skills` -> this repo's `skills/`
- `~/.codex/skills/<skill>` -> `~/.agents/skills/<skill>`
- `~/.claude/skills/<skill>` -> `~/.agents/skills/<skill>`

After pulling updates:

```bash
git pull
./scripts/install-bridges.sh
```

Restart new Claude Code / Codex sessions so they reload the skill list.

