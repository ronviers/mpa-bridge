from pathlib import Path

from mpa_bridge import artifacts, validate_single
from mpa_bridge.diagnostics import Severity, has_errors

FIX = Path(__file__).parent / "fixtures"


def _validate(name: str):
    doc = artifacts.load(FIX / name)
    kind = artifacts.identify(doc)
    return validate_single.validate(doc, kind, source=name), kind


def test_spec_valid_no_errors():
    diags, kind = _validate("spec_minimal_valid.json")
    assert kind == "spec"
    errors = [d for d in diags if d.severity is Severity.ERROR]
    assert errors == [], f"unexpected errors: {[d.format() for d in errors]}"


def test_spec_missing_demand_fires_inv7():
    diags, _ = _validate("spec_missing_demand.json")
    codes = {d.code for d in diags if d.severity is Severity.ERROR}
    assert "RFC1.INV.7" in codes


def test_signature_valid_no_errors():
    diags, kind = _validate("signature_s_valid.json")
    assert kind == "signature"
    assert not has_errors(diags), [d.format() for d in diags]


def test_signature_domain_violation_fires_inv7():
    diags, _ = _validate("signature_domain_violation.json")
    codes = {d.code for d in diags if d.severity is Severity.ERROR}
    assert "RFC2.INV.7" in codes


def test_driver_minimal_valid_no_errors():
    diags, kind = _validate("driver_minimal_valid.json")
    assert kind == "driver_profile"
    assert not has_errors(diags), [d.format() for d in diags]


def test_rdoc_minimal_valid_no_errors():
    diags, kind = _validate("rdoc_minimal_valid.json")
    assert kind == "r_doc"
    assert not has_errors(diags), [d.format() for d in diags]
