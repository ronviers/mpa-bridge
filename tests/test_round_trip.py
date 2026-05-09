"""Component 4: round-trip checker tests.

Identity round-trip (target == measured) should produce only INFO diagnostics.
Forward-error and round-trip-error against thresholds verified for I1 and I5;
I2/I3/I4 emit METRIC_NA infos rather than error.
"""

import json
from pathlib import Path

from mpa_bridge import artifacts, round_trip
from mpa_bridge.diagnostics import Severity

FIX = Path(__file__).parent / "fixtures"


def _rdoc_with_intent(intent: str) -> dict:
    rdoc = artifacts.load(FIX / "rdoc_minimal_valid.json")
    rdoc["intent"] = intent
    return rdoc


def _identity_measured(rdoc: dict) -> list[dict]:
    """Each measurement equals its target — perfect identity round-trip."""
    return [dict(t) for t in rdoc["signature_targets"]]


def _run(rdoc: dict, measured: list[dict], tmp_path: Path) -> tuple[int, list[str]]:
    rdoc_path = tmp_path / "rdoc.json"
    rdoc_path.write_text(json.dumps(rdoc), encoding="utf-8")
    measured_paths = []
    for i, m in enumerate(measured):
        p = tmp_path / f"m_{i}.json"
        p.write_text(json.dumps(m), encoding="utf-8")
        measured_paths.append(str(p))
    rc = round_trip.run(str(rdoc_path), measured_paths)
    return rc, measured_paths


def test_i1_identity_passes(tmp_path, capsys):
    rdoc = _rdoc_with_intent("I1")
    rc, _ = _run(rdoc, _identity_measured(rdoc), tmp_path)
    assert rc == 0
    out = capsys.readouterr().out
    assert "RFC-S5.INTENT" in out
    assert "regime-mismatch" in out


def test_i1_regime_mismatch_fires_forward(tmp_path, capsys):
    rdoc = _rdoc_with_intent("I1")
    measured = _identity_measured(rdoc)
    measured[0]["regime_class"] = "r"  # was "c"; threshold=0.1, distance=1.0
    rc, _ = _run(rdoc, measured, tmp_path)
    assert rc == 1
    out = capsys.readouterr().out
    assert "RFC-S5.FORWARD" in out
    assert "exceeds threshold" in out


def test_i5_identity_passes(tmp_path, capsys):
    rdoc = _rdoc_with_intent("I5")
    rc, _ = _run(rdoc, _identity_measured(rdoc), tmp_path)
    assert rc == 0


def test_i5_universality_class_disagreement_is_infinite(tmp_path, capsys):
    rdoc = _rdoc_with_intent("I5")
    measured = _identity_measured(rdoc)
    measured[0]["regime_class"] = "s"  # different universality class
    measured[0]["universality_tuple"] = {"alpha_s": 0.6, "P_s": 0.5}
    rc, _ = _run(rdoc, measured, tmp_path)
    assert rc == 1
    out = capsys.readouterr().out
    assert "RFC-S5.FORWARD" in out
    assert "inf" in out  # disagreement → +inf


def test_i2_marked_metric_na(tmp_path, capsys):
    rdoc = _rdoc_with_intent("I2")
    rc, _ = _run(rdoc, _identity_measured(rdoc), tmp_path)
    out = capsys.readouterr().out
    assert "RFC-S5.METRIC_NA" in out
    assert rc == 0  # info, not error


def test_missing_measurement_fires_coverage(tmp_path, capsys):
    rdoc = _rdoc_with_intent("I1")
    measured = _identity_measured(rdoc)
    measured.pop()  # drop last (the e1 target)
    rc, _ = _run(rdoc, measured, tmp_path)
    assert rc == 1
    out = capsys.readouterr().out
    assert "RFC-S5.MISSING" in out
