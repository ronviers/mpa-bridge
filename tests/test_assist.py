"""Test the assist surface with the API call mocked.

Real-API tests would burn cache + cost; the cache file *is* the integration
test artifact. Unit tests just verify the cache round-trip behavior and
that gap_report routes through ask() correctly.
"""

import json
from pathlib import Path

from mpa_bridge import assist, gap_report


def test_cache_hit_skips_api(tmp_path, monkeypatch):
    monkeypatch.setattr(assist, "CACHE_DIR", tmp_path)

    # Pre-populate cache (key includes max_tokens)
    import hashlib
    key = hashlib.sha256(f"{assist.HAIKU}\n2048\nsys-x\nprompt-y".encode("utf-8")).hexdigest()
    (tmp_path / f"{key}.json").write_text(json.dumps({"response": "cached!"}), encoding="utf-8")

    # If this dispatches to the API the test would fail (no key shim); cache should hit.
    out = assist.ask("prompt-y", system="sys-x", model=assist.HAIKU, max_tokens=2048)
    assert out == "cached!"


def test_gap_report_uses_assist(tmp_path, monkeypatch, capsys):
    """gap_report.run() reads atlas + data, calls ask(), prints result."""
    captured = {}

    def fake_ask(prompt, system="", model=assist.HAIKU, max_tokens=2048):
        captured["prompt"] = prompt
        captured["system"] = system
        captured["model"] = model
        return "GAP_REPORT_BODY"

    monkeypatch.setattr(gap_report.assist, "ask", fake_ask)

    data_file = tmp_path / "data.md"
    data_file.write_text("Stabilizer-graph data, p ≈ 0.005, distance-3.", encoding="utf-8")

    rc = gap_report.run(str(data_file))
    assert rc == 0
    assert capsys.readouterr().out.strip() == "GAP_REPORT_BODY"

    # System prompt must include v9 and reference drivers.
    assert "## v9" in captured["system"]
    assert "## reference drivers" in captured["system"]
    assert "surface-code-qec" in captured["system"]
    assert "Stabilizer-graph data" in captured["prompt"]
    assert captured["model"] == assist.HAIKU
