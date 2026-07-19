# Agent Skill Source Of Truth

This repository is the local source of truth for user-maintained agent skills.

## Canonical Skill Source

- Canonical directory: `skills/`
- Shared local alias: `~/.agents/skills -> <this-repo>/skills`

Edit user-maintained skills only in `skills/<skill-name>/`. Host-specific skill
directories are bridge layers, not maintenance layers.

## Host Bridges

The installer maintains these host integrations:

- Codex: `~/.codex/skills/<skill> -> ~/.agents/skills/<skill>`
- Claude Code skills: `~/.claude/skills/<skill> -> ~/.agents/skills/<skill>`
- Claude Code commands: selected `~/.claude/commands/*.md` files point to the
  canonical `SKILL.md` files.
- OpenClaw Codex: `~/.openclaw/acpx/codex-home/skills/<skill> -> ~/.agents/skills/<skill>`
- Hermes personal and automation profiles: `skills.external_dirs` includes
  `~/.agents/skills`
- Hermes same-name local/builtin shadows: known local copies such as
  `creative/humanizer` are bridged back to `~/.agents/skills/<skill>` so the
  truth-source version wins.
- cc-switch Claude providers: `skillListingBudgetFraction` is set to `0.05`
  so Claude-launched sessions keep enough prompt budget for skill discovery.

Platform-owned system skills are allowed to stay host-local. Do not replace
host `.system` directories.

## Repair And Verify

Run this after creating, editing, pulling, or moving skills:

```bash
./scripts/install-bridges.sh --strict
```

This command repairs bridges, regenerates Claude Code command bridges, updates
Hermes and cc-switch configuration when needed, and then runs the all-host audit.

For audit only:

```bash
./scripts/audit-agent-skill-hosts.sh --strict
```

## Drift Rule

If a user-maintained functional skill appears as a real local directory under a
host directory, promote it into `skills/` and rerun the installer. Do not keep
long-term skill logic in:

- `~/.codex/skills`
- `~/.claude/skills`
- `~/.openclaw/acpx/codex-home/skills`
- Hermes profile-local skill directories

After bridge changes, restart already-running Claude Code, Codex, OpenClaw, or
Hermes sessions. Existing sessions may keep a cached skill or command list.
