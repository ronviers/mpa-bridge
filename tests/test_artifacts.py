from pathlib import Path

from mpa_bridge import artifacts

FIX = Path(__file__).parent / "fixtures"


def test_identify_spec():
    doc = artifacts.load(FIX / "spec_minimal_valid.json")
    assert artifacts.identify(doc) == "spec"


def test_identify_signature():
    doc = artifacts.load(FIX / "signature_s_valid.json")
    assert artifacts.identify(doc) == "signature"


def test_identify_driver_profile():
    doc = artifacts.load(FIX / "driver_minimal_valid.json")
    assert artifacts.identify(doc) == "driver_profile"


def test_identify_r_doc():
    doc = artifacts.load(FIX / "rdoc_minimal_valid.json")
    assert artifacts.identify(doc) == "r_doc"


def test_identify_unknown():
    assert artifacts.identify({"foo": "bar"}) == "unknown"
