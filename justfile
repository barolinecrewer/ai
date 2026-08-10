set shell := ["bash", "-uc"]

dotfiles := justfile_directory()

# Sync shared AI assistant config from .general into Claude Code and Codex layouts.
sync-ai-config:
    mkdir -p .claude/commands .claude/skills .codex/skills
    test ! -d .general/commands || rsync -a --delete .general/commands/ .claude/commands/
    test ! -d .general/skills || rsync -a --delete .general/skills/ .claude/skills/
    test ! -d .general/skills || rsync -a --delete .general/skills/ .codex/skills/
    if [[ -d .general/commands ]]; then for command_file in .general/commands/*.md; do [[ -e "$command_file" ]] || continue; skill_name="$(basename "$command_file" .md)"; mkdir -p ".codex/skills/$skill_name"; rsync -a "$command_file" ".codex/skills/$skill_name/SKILL.md"; done; fi
    test ! -f .general/instructions.md || rsync -a .general/instructions.md CLAUDE.md
    test ! -f .general/instructions.md || rsync -a .general/instructions.md AGENTS.md
    test ! -f .general/CLAUDE.md || rsync -a .general/CLAUDE.md CLAUDE.md
    test ! -f .general/AGENTS.md || rsync -a .general/AGENTS.md AGENTS.md
    test ! -f .general/settings.json || python3 .general/generate-settings.py

xbar:
    mkdir -p "$HOME/Library/Application Support/xbar/plugins"
    cp "{{dotfiles}}/xbar/plugins/"* "$HOME/Library/Application Support/xbar/plugins/"
    chmod +x "$HOME/Library/Application Support/xbar/plugins/"*
