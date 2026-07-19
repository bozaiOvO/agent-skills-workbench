# Agent Skills Workbench

This repository is the source of truth for shared local agent skills.

## Layout

- `skills/`: human-maintained skill source.
- `SOURCE_OF_TRUTH.md`: the contract for shared user skills across agent hosts.
- `scripts/install-bridges.sh`: creates symlink bridges for local agent hosts.
- `scripts/install-claude-commands.sh`: creates Claude Code slash command bridges for key user skills.
- `scripts/audit-agent-skill-hosts.sh`: audits Codex, Claude Code, OpenClaw, Hermes, cc-switch, and DBS routes together.
- `scripts/audit-skill-bridges.sh`: fails when user skills drift into host-local directories.
- `scripts/audit-skill-routes.sh`: fails when DBS routes reference missing skills.
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
- `~/.openclaw/acpx/codex-home/skills/<skill>` -> `~/.agents/skills/<skill>` when OpenClaw is installed

It also keeps Hermes profiles pointed at `~/.agents/skills`, repairs cc-switch
Claude provider skill-listing budget, and regenerates Claude Code slash command
bridges.

After pulling updates:

```bash
git pull
./scripts/install-bridges.sh
```

Restart new Claude Code / Codex sessions so they reload the skill list.

## Drift Rule

Platform/system skills are allowed to differ between hosts. User-maintained
skills should not differ. If Claude Code or Codex installs a functional skill as
a real local directory under `~/.claude/skills` or `~/.codex/skills`, promote it
into `skills/` and rerun:

```bash
./scripts/install-bridges.sh
./scripts/audit-skill-bridges.sh
./scripts/audit-agent-skill-hosts.sh
./scripts/audit-skill-routes.sh
```
