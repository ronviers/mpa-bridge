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


def test_spec_missing_demand_fires_schema_error():
    diags, _ = _validate("spec_missing_demand.json")
    errors = [d for d in diags if d.severity is Severity.ERROR]
    assert any(d.code == "SCHEMA.spec" and "demand_envelope" in d.message for d in errors), \
        [d.format() for d in errors]


def test_signature_valid_no_errors():
    diags, kind = _validate("signature_s_valid.json")
    assert kind == "signature"
    assert not has_errors(diags), [d.format() for d in diags]


def test_signature_domain_violation_fires_schema_error():
    diags, _ = _validate("signature_domain_violation.json")
    errors = [d for d in diags if d.severity is Severity.ERROR]
    assert any(d.code == "SCHEMA.signature" for d in errors), [d.format() for d in errors]


def test_driver_minimal_valid_no_errors():
    diags, kind = _validate("driver_minimal_valid.json")
    assert kind == "driver_profile"
    assert not has_errors(diags), [d.format() for d in diags]


def test_rdoc_minimal_valid_no_errors():
    diags, kind = _validate("rdoc_minimal_valid.json")
    assert kind == "r_doc"
    assert not has_errors(diags), [d.format() for d in diags]


def test_rdoc_signature_targets_validated_via_schema_ref():
    """RFC-RI §2: signature_targets are full RFC-2 FDR signatures.
    Schema $ref propagates the regime-conditional 'X_c required' constraint.
    """
    from mpa_bridge import artifacts, validate_single
    from mpa_bridge.diagnostics import Severity
    doc = artifacts.load(FIX / "rdoc_minimal_valid.json")
    doc["signature_targets"][1]["universality_tuple"] = {}  # drop X_c
    diags = validate_single.validate(doc, "r_doc", source="t")
    errors = [d for d in diags if d.severity is Severity.ERROR and d.code == "SCHEMA.r_doc"]
    assert errors, [d.format() for d in diags]
    assert any("signature_targets" in d.path and "1" in d.path for d in errors), \
        [d.path for d in errors]
