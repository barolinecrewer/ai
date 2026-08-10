# AI Assistant Config

This repo keeps shared assistant assets in `.general/` and uses `just sync-ai-config` to push them into the Claude Code and Codex layouts. Everything under `.claude/` and `.codex/` that is *not* generated (native config, hooks) is committed directly in those folders instead of mirrored through `.general/`.

## Source Layout

```text
.general/
  commands/              # Shared command-style prompts
  skills/                # Shared SKILL.md-based workflows
  settings.json          # Single settings source, keyed by "security" / "claude" / "codex"
  generate-settings.py   # Turns settings.json's claude/codex keys into native config files
  instructions.md        # Optional shared root instructions
  CLAUDE.md              # Optional Claude-specific root instructions
  AGENTS.md              # Optional Codex-specific root instructions
```

## Generated Layout

`just sync-ai-config` maps shared files to each assistant format:

```text
.general/commands/*.md -> .claude/commands/*.md
.general/commands/*.md -> .codex/skills/<command>/SKILL.md

.general/skills/* -> .claude/skills/*
.general/skills/* -> .codex/skills/*

.general/instructions.md -> CLAUDE.md
.general/instructions.md -> AGENTS.md
.general/CLAUDE.md       -> CLAUDE.md
.general/AGENTS.md       -> AGENTS.md

.general/settings.json -> .claude/settings.json   (the "claude" key, via generate-settings.py)
.general/settings.json -> .codex/config.toml      (the "codex" key, via generate-settings.py)
```

## Settings

`.general/settings.json` is the single settings source. It has three top-level keys:

- `security` — shared intent, documentation only (nothing reads this key directly; it's the paths/commands the `claude.permissions.deny` list below was derived from).
- `claude` — dumped as-is into `.claude/settings.json`.
- `codex` — dumped as flat `key = value` TOML lines into `.codex/config.toml`.

`generate-settings.py` does not attempt to convert one tool's settings into the other's schema — Claude's `permissions`/`enabledPlugins` have no Codex equivalent and Codex's `sandbox_mode` has no Claude equivalent, so each only exists under its own key. Add a field under `claude` or `codex` and re-run the sync; there's no cross-tool mapping to keep in sync by hand anymore.

Both generated files are overwritten on every sync — edit `.general/settings.json`, not `.claude/settings.json` or `.codex/config.toml` directly.

### Codex deny list — not implemented, here's why

Claude's `permissions.deny` blocks reads/commands by glob (`Bash(cat *.env)`). Codex has no direct equivalent, and porting the `security` block over is not a small change. Researched against the installed `codex-cli` source (v0.145/0.147) and tested live via `codex execpolicy check`:

- **`.codex/rules/*.rules`** (Starlark `prefix_rule(pattern=[...], decision="forbidden")`) — real, confirmed working. But it only matches literal command-*token* prefixes, no glob on arguments. It can forbid `op` entirely; it cannot forbid `cat` only when the argument looks like `*.env`.
- **`[permissions.<profile>.filesystem]`** in `config.toml` — real glob-keyed deny (`"**/*.env" = "deny"`) enforced by the OS sandbox (Seatbelt/bwrap), closer to Claude's behavior. But a custom profile does **not** inherit the built-in `workspace-write` profile's grants — per `compile_permission_profile` in `codex-rs`, it starts from a fully-restricted baseline, so setting `default_permissions` to a custom profile with only deny entries would silently lock down normal read/write access everywhere else, not just the denied globs.

Closing that gap properly means either accepting the blunter whole-command `execpolicy` blocks, or fully re-deriving and replicating the built-in `workspace-write` profile's grants inside a custom profile (undone research: the exact glob set that profile uses). Revisit if Codex adds profile inheritance from builtins, or if the blunter `execpolicy` blocks turn out to be good enough.

## Tool-Native Files

Files that only make sense for one assistant and aren't part of `settings.json` live directly in that assistant's folder and are committed as-is — they are never generated from `.general/`:

```text
.codex/hooks.json   # Codex hooks
```

Claude-only folders (`agents/`, `agent-memory/`, `output-styles/`, `rules/`, `workflows/`) are omitted entirely rather than kept as empty placeholders — add one back (with real content) if you start using that feature.

## Commands as Codex Skills

Claude command files stay commands. Codex gets those same command prompts as skills because command-style workflows are more durable as `SKILL.md` files in Codex.

Example:

```text
.general/commands/exec-ready.md -> .codex/skills/exec-ready/SKILL.md
```

## Usage

Preview the sync:

```sh
just --dry-run sync-ai-config
```

Run the sync:

```sh
just sync-ai-config
```
