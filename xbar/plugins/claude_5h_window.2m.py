#!/usr/bin/env python3

# <xbar.title>Claude Code 5-Hour Window</xbar.title>
# <xbar.version>v2.0</xbar.version>
# <xbar.desc>Shows time and token budget remaining in Claude Code's active 5-hour billing block</xbar.desc>
# <xbar.dependencies>python,node</xbar.dependencies>

import json
import subprocess
import os
import glob
from datetime import datetime, timezone
from typing import Any, Optional

# Optional: hard-code a token ceiling if you know one you like (e.g. from a plan
# doc or your own comfort level). Leave as None to auto-estimate the ceiling
# from your highest completed block in the last 3 days instead - mirrors what
# `ccusage blocks --token-limit max` does, just computed locally each refresh.
TOKEN_LIMIT: Optional[int] = None


# Base64 PNG shown in the menu bar. Using xbar's "image" param (not
# "templateImage") so the icon's own colors are preserved as-is - the
# tradeoff is it won't auto-tint for light/dark menu bar mode the way a
# template image would. Swap ICON_B64 below for your own icon's base64 data.
ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAABYAAAAWCAYAAADEtGw7AAAAAXNSR0IArs4c6QAAAHhlWElmTU0AKgAAAAgABAEaAAUAAAABAAAAPgEbAAUAAAABAAAARgEoAAMAAAABAAIAAIdpAAQAAAABAAAATgAAAAAAAABIAAAAAQAAAEgAAAABAAOgAQADAAAAAQABAACgAgAEAAAAAQAAABagAwAEAAAAAQAAABYAAAAAL64HbQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAn5JREFUOBHtUjFrVEEQnt239+7eJWIlChG5SDRoJIKFgrWNoKXkEAUrSWN7sQkcWOkv0FSpRAl2llY2ksLCkCDPSIRgRE0wRTzusvfejvNt3OclVySNXQb27b6Z7/tmdmaJDu1/d0CFBMykPjZujwxUOLY2eA+2xzFRq6PsuSfPPytFDFYhvPzgepmrR99rTaOZ87GDqQrKaEW5ozRL8ktjzTlflullM3FJkzbyoTiKqJPlxHKVf+n/ouGS0iomIpvnElaUkSv1aonELmPts/Nqu5s9c8S/IQrt3gUfYsDkjlfBEdt1zUJ4ZPunQxTXEpHFs49fTpJTm1oq22veJzFggAUHdp7WvQbO6lvzZhWHjY4rx3xkfjCOzrRs9sZpW9ccf4iUGpKqACkswq2Y15yyF7WLXwzE5tqWzZcrSedymXLfY5U2JlbAYGmU5B2S3pWkr21x/ZB1UtauOch/sEwOX2UdF04inK6kXxMNX4WpxmYYSPyFYUmGRCqt7fM6jLSgJpX7AaOgxEQ1EfZm2jZ/hxMrRqfGZUl2ogyffSwk9mJySxnmgmLl+xwS0NKtsdicvrBgtJZ3XMxgH+mdsHBIOGm2sjg+Nrfke1y8ivjEKfQ4AQhTT0oGr0res/Zn/IcFH2L4BxYccKERKikGM/J9MEuHqWmdm3TsjrW7PCOcaZvza8qzeWnkDkkp6ZG6IrEbcvVH0sT71ql1eThPR0UjCPft6VR95tPDibcIpFMTm2mjfncvCD7E4AcWnL2YohUhIHW12fHWl+a9ilS1IbPomyJ8iAEDLDiBH/Y+4agVTVe0uVNrzm4r5a7+svwqgMMOH2LAAAtOiB3ufR34A3v5I7DID3eIAAAAAElFTkSuQmCC"
)


def format_number(num: float) -> str:
    sign = "-" if num < 0 else ""
    num = abs(num)
    if num >= 1_000_000:
        return f"{sign}{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{sign}{num / 1_000:.1f}K"
    return f"{sign}{int(num)}"


def format_duration(seconds: float) -> str:
    if seconds <= 0:
        return "0m"
    hours, remainder = divmod(int(seconds), 3600)
    minutes = remainder // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def get_blocks_data() -> dict[str, Any]:
    """Fetches Claude Code's 5-hour block data using `npx ccusage@latest blocks -j`."""
    try:
        env = os.environ.copy()

        common_paths = [
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
            "/opt/homebrew/bin",  # Homebrew on Apple Silicon
            os.path.expanduser("~/.nvm/versions/node/*/bin"),  # NVM paths
            os.path.expanduser("~/node_modules/.bin"),
        ]

        expanded_paths = []
        for path in common_paths:
            if "*" in path:
                expanded_paths.extend(glob.glob(path))
            elif os.path.exists(path):
                expanded_paths.append(path)

        current_path = env.get("PATH", "")
        for path in expanded_paths:
            if path not in current_path:
                current_path = f"{path}:{current_path}"
        env["PATH"] = current_path

        # --recent limits to the last 3 days, which is plenty for estimating
        # a per-block ceiling and keeps the JSONL parse fast.
        result = subprocess.run(
            ["npx", "ccusage@latest", "blocks", "--recent", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=env,
        )

        if result.returncode == 0:
            return json.loads(result.stdout)

        return {
            "error": f"Command failed with code {result.returncode}",
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 30 seconds"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode error: {e}"}
    except FileNotFoundError:
        return {"error": "npx command not found - Node.js may not be installed"}


def parse_iso(ts: str) -> datetime:
    """Parses ccusage's ISO 8601 timestamps (which end in 'Z')."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def block_total_tokens(block: dict[str, Any]) -> float:
    token_counts = block.get("tokenCounts", {}) or {}
    if token_counts:
        return sum(token_counts.values())
    return block.get("totalTokens", 0)


def estimate_token_limit(blocks: list[dict[str, Any]], active_id: Optional[str]) -> Optional[int]:
    """Highest completed block's token total, mirroring `-t max` in ccusage."""
    completed_totals = [
        block_total_tokens(b) for b in blocks if not b.get("isActive") and b.get("id") != active_id
    ]
    if not completed_totals:
        return None
    return int(max(completed_totals))


def main() -> None:
    data = get_blocks_data()

    if not data or (isinstance(data, dict) and "error" in data):
        print(f" error | image={ICON_B64} color=red")
        print("---")
        if isinstance(data, dict) and "error" in data:
            print(f"Error: {data['error']}")
            if data.get("stderr"):
                print(f"Stderr: {data['stderr']}")
        else:
            print("Failed to fetch usage data")
        return

    blocks = data.get("blocks", [])
    active = next((b for b in blocks if b.get("isActive")), None)

    if not active:
        print(f" idle | image={ICON_B64}")
        print("---")
        print("No active 5-hour window")
        print("Starts on your next Claude Code message")
        return

    now = datetime.now(timezone.utc)
    start = parse_iso(active["startTime"])
    end = parse_iso(active["endTime"])
    remaining_seconds = (end - now).total_seconds()
    elapsed_seconds = max((now - start).total_seconds(), 1)

    total_tokens = block_total_tokens(active)
    cost = active.get("costUSD", 0) or 0
    models = active.get("models", [])
    burn_rate_per_min = total_tokens / (elapsed_seconds / 60)

    limit = TOKEN_LIMIT if TOKEN_LIMIT else estimate_token_limit(blocks, active.get("id"))
    limit_is_estimate = TOKEN_LIMIT is None and limit is not None

    tokens_remaining = None
    pct_remaining = None
    if limit:
        tokens_remaining = max(limit - total_tokens, 0)
        pct_remaining = max(min(tokens_remaining / limit * 100, 100), 0)

    # Color by whichever signal - time or token budget - is closer to running out
    time_urgent = remaining_seconds <= 30 * 60
    time_warn = remaining_seconds <= 60 * 60
    tokens_urgent = pct_remaining is not None and pct_remaining <= 10
    tokens_warn = pct_remaining is not None and pct_remaining <= 25

    if time_urgent or tokens_urgent:
        color = "red"
    elif time_warn or tokens_warn:
        color = "orange"
    else:
        color = None  # let the text inherit the system's adaptive color

    remaining_str = format_duration(remaining_seconds)
    toolbar_text = remaining_str
    if pct_remaining is not None:
        # Use a middle dot, not "|" - xbar treats everything after the FIRST
        # "|" on a line as key=value attributes, so a second "|" here would
        # break parsing (e.g. "unknown parameter: 34% left | color").
        toolbar_text += f" \u00b7 {pct_remaining:.0f}% left"

    # color is only set when urgent (orange/red); otherwise it's left unset
    # so the text itself auto-adapts (white on dark menu bars, black on light
    # ones) rather than hardcoding white, which would go invisible in light
    # mode. This only affects the text - the icon's own colors are fixed
    # since we're using "image" rather than "templateImage".
    attrs = [f"image={ICON_B64}"]
    if color:
        attrs.append(f"color={color}")
    print(f" {toolbar_text} | {' '.join(attrs)}")
    print("---")
    print("5-Hour Window")
    print(f"Started: {start.astimezone().strftime('%I:%M %p')}")
    print(f"Resets: {end.astimezone().strftime('%I:%M %p')}")
    print(f"Time remaining: {remaining_str}")
    print("---")
    print(f"Tokens used: {format_number(total_tokens)}")
    if limit:
        label = "Est. limit" if limit_is_estimate else "Limit"
        print(f"{label}: {format_number(limit)}")
        print(f"Tokens remaining: {format_number(tokens_remaining)} ({pct_remaining:.0f}%)")
    else:
        print("Tokens remaining: no history yet to estimate a ceiling")
    print(f"Burn rate: {format_number(burn_rate_per_min)}/min")
    if cost:
        print(f"Cost so far: ${cost:.2f}")
    if models:
        print(f"Models: {', '.join(models)}")
    print("---")
    print("Refresh | refresh=true")


if __name__ == "__main__":
    main()