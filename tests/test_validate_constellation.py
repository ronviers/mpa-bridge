from pathlib import Path

from mpa_bridge import artifacts, validate_constellation
from mpa_bridge.diagnostics import Severity, has_errors

FIX = Path(__file__).parent / "fixtures"


def _load_all():
    spec = artifacts.load(FIX / "spec_minimal_valid.json")
    driver = artifacts.load(FIX / "driver_minimal_valid.json")
    rdoc = artifacts.load(FIX / "rdoc_minimal_valid.json")
    return spec, driver, rdoc


def test_constellation_valid():
    spec, driver, rdoc = _load_all()
    diags = validate_constellation.validate(spec, driver, rdoc, signatures=[])
    assert not has_errors(diags), [d.format() for d in diags]


def test_c1_d_outside_gamut():
    spec, driver, rdoc = _load_all()
    spec["D"] = {"form": "point", "value": 1000.0}  # outside [1, 100]
    diags = validate_constellation.validate(spec, driver, rdoc, signatures=[])
    codes = {d.code for d in diags if d.severity is Severity.ERROR}
    assert "RFC3.C1" in codes


def test_c3_intent_not_supported():
    spec, driver, rdoc = _load_all()
    driver["intents"]["I1"]["supported"] = False
    diags = validate_constellation.validate(spec, driver, rdoc, signatures=[])
    codes = {d.code for d in diags if d.severity is Severity.ERROR}
    assert "RFC3.C3" in codes


def test_c4_realizer_class_mismatch():
    spec, driver, rdoc = _load_all()
    rdoc["realizer_class_target"] = "habit-extinction"
    diags = validate_constellation.validate(spec, driver, rdoc, signatures=[])
    codes = {d.code for d in diags if d.severity is Severity.ERROR}
    assert "RFC3.C4" in codes


def test_k1_missing_signature_target():
    spec, driver, rdoc = _load_all()
    rdoc["signature_targets"] = [t for t in rdoc["signature_targets"] if t["object_ref"] != "v2"]
    diags = validate_constellation.validate(spec, driver, rdoc, signatures=[])
    codes = {d.code for d in diags if d.severity is Severity.ERROR}
    assert "RFC3.K1" in codes
