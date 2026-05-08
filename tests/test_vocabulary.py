from mpa_bridge import vocabulary
from mpa_bridge.diagnostics import Severity


def test_lowercase_regime_clean():
    text = "The regime is $c$ committed, with $s$ suspended and $r$ reset."
    diags = vocabulary.check_text(text, source="t")
    codes = {d.code for d in diags if d.severity is Severity.WARNING}
    assert "RFCV.S2.regimes" not in codes


def test_uppercase_prose_regime_fires():
    text = "The regime C is committed under the operator algebra."
    diags = vocabulary.check_text(text, source="t")
    codes = {d.code for d in diags if d.severity is Severity.WARNING}
    assert "RFCV.S2.regimes" in codes


def test_compress_glyph_collision_fires():
    text = "The compression operator $C$ contracts the tower geometrically."
    diags = vocabulary.check_text(text, source="t")
    codes = {d.code for d in diags if d.severity is Severity.WARNING}
    assert "RFCV.S4.compress" in codes


def test_varepsilon_subscript_warning():
    text = r"At each ascent, $\varepsilon$ contracts the tower."
    diags = vocabulary.check_text(text, source="t")
    codes = {d.code for d in diags if d.severity is Severity.WARNING}
    assert "RFCV.S4.epsilon" in codes


def test_coverage_emitted():
    text = "Mentions $c$ and $\\mathcal{C}$ and I1 in passing."
    diags = vocabulary.check_text(text, source="t")
    codes = {d.code for d in diags if d.severity is Severity.INFO}
    assert "RFCV.COVERAGE" in codes
