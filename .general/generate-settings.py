import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
src = json.loads((root / ".general/settings.json").read_text())

(root / ".claude/settings.json").write_text(
    json.dumps(src.get("claude", {}), indent=2) + "\n"
)


def toml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, list):
        return "[" + ", ".join(toml_value(i) for i in v) + "]"
    return str(v)


codex = src.get("codex", {})
lines = [
    "# Generated from .general/settings.json by `just sync-ai-config`. Edit the source, not this file."
]
lines += [f"{k} = {toml_value(v)}" for k, v in codex.items()]
(root / ".codex/config.toml").write_text("\n".join(lines) + "\n")
