"""Thin Claude-call surface.

One function: ``ask(prompt, system, model)``. Cache files at
``D:\\Cache\\mpa-bridge\\`` double as gradable run records — each is a JSON
blob with model, system, prompt, response, timestamp.

This is the only place mpa-bridge talks to a model. Used by the synthesis
surfaces (components 3, 5, 6); validators stay mechanical.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic

CACHE_DIR = Path(r"D:\Cache\mpa-bridge")


def _ensure_api_key() -> None:
    """Populate ANTHROPIC_API_KEY from HKCU\\Environment if process env is stale.

    Windows-only fallback. setx writes to the registry but the current
    process inherits its env at launch — same gotcha the GWS1 profiler
    handles via read_windows_user_env. Without this, mpa-bridge fails
    whenever Claude Code (or any shell) was launched before the key was set.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    if sys.platform != "win32":
        return
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
            value, _ = winreg.QueryValueEx(h, "ANTHROPIC_API_KEY")
            if value:
                os.environ["ANTHROPIC_API_KEY"] = value
    except OSError:
        pass

HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-4-6"
OPUS = "claude-opus-4-7"


def ask(prompt: str, system: str = "", model: str = HAIKU, max_tokens: int = 2048) -> str:
    """Call Claude. Hit cache if the (model, system, prompt) tuple was seen before."""
    key = hashlib.sha256(f"{model}\n{max_tokens}\n{system}\n{prompt}".encode("utf-8")).hexdigest()
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))["response"]

    _ensure_api_key()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set (checked process env and HKCU\\Environment)."
        )

    client = anthropic.Anthropic()
    system_blocks = (
        [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        if system
        else []
    )
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_blocks,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "\n".join(b.text for b in msg.content if b.type == "text")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "model": model,
        "system": system,
        "prompt": prompt,
        "response": text,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "usage": {
            "input_tokens": msg.usage.input_tokens,
            "output_tokens": msg.usage.output_tokens,
            "cache_creation_input_tokens": getattr(msg.usage, "cache_creation_input_tokens", 0),
            "cache_read_input_tokens": getattr(msg.usage, "cache_read_input_tokens", 0),
        },
    }
    cache_file.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return text
