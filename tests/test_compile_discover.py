"""Tests for compile + discover (with assist.ask mocked)."""

import json
from pathlib import Path

from mpa_bridge import artifacts, assist, compile_, discover

FIX = Path(__file__).parent / "fixtures"


def test_discover_reads_drivers_and_calls_assist(tmp_path, monkeypatch, capsys):
    captured = {}

    def fake_ask(prompt, system="", model=assist.HAIKU, max_tokens=2048):
        captured["system"] = system
        captured["prompt"] = prompt
        captured["model"] = model
        return "## surface-code-qec\n- score: 87\n- gamut: covers\n"

    monkeypatch.setattr(discover.assist, "ask", fake_ask)

    data_file = tmp_path / "data.md"
    data_file.write_text("Stabilizer time-series.", encoding="utf-8")

    rc = discover.run(str(data_file))
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert "surface-code-qec" in out
    assert captured["model"] == assist.HAIKU
    assert "surface-code-qec" in captured["system"]
    assert "Stabilizer time-series" in captured["prompt"]


def test_compile_rejects_invalid_spec(tmp_path, monkeypatch, capsys):
    """If the spec doesn't pass component 1, compile should not call Claude."""
    called = []

    def fake_ask(*a, **kw):
        called.append(True)
        return "{}"

    monkeypatch.setattr(compile_.assist, "ask", fake_ask)

    rc = compile_.run(
        spec_path=str(FIX / "spec_missing_demand.json"),
        intent="I1",
        driver_path=str(FIX / "driver_minimal_valid.json"),
    )
    assert rc == 1
    assert called == [], "compile must early-out when spec is invalid"


def test_compile_validator_gatekeeps_bad_rdoc(tmp_path, monkeypatch, capsys):
    """A compiler response missing required fields must produce r_doc errors."""

    def fake_ask(*a, **kw):
        return json.dumps({"spec_ref": "x", "intent": "I1"})  # missing most fields

    monkeypatch.setattr(compile_.assist, "ask", fake_ask)

    rc = compile_.run(
        spec_path=str(FIX / "spec_minimal_valid.json"),
        intent="I1",
        driver_path=str(FIX / "driver_minimal_valid.json"),
    )
    assert rc == 1
    err = capsys.readouterr().err
    assert "SCHEMA.r_doc" in err  # validator-gatekeeper fired via schema


def test_compile_writes_rdoc_to_output(tmp_path, monkeypatch):
    valid_rdoc = artifacts.load(FIX / "rdoc_minimal_valid.json")

    def fake_ask(*a, **kw):
        return json.dumps(valid_rdoc)

    monkeypatch.setattr(compile_.assist, "ask", fake_ask)

    out_path = tmp_path / "rdoc.json"
    rc = compile_.run(
        spec_path=str(FIX / "spec_minimal_valid.json"),
        intent="I1",
        driver_path=str(FIX / "driver_minimal_valid.json"),
        output_path=str(out_path),
    )
    assert rc == 0
    assert out_path.exists()
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written["spec_ref"] == valid_rdoc["spec_ref"]


def test_compile_handles_fenced_json(monkeypatch, capsys):
    """Fallback parser strips ```json``` fences if Sonnet ignores instructions."""
    valid_rdoc = artifacts.load(FIX / "rdoc_minimal_valid.json")
    fenced = f"```json\n{json.dumps(valid_rdoc)}\n```"

    def fake_ask(*a, **kw):
        return fenced

    monkeypatch.setattr(compile_.assist, "ask", fake_ask)

    rc = compile_.run(
        spec_path=str(FIX / "spec_minimal_valid.json"),
        intent="I1",
        driver_path=str(FIX / "driver_minimal_valid.json"),
    )
    assert rc == 0
