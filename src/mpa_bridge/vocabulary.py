"""Component 7: RFC-V vocabulary checker.

v0.1 ships narrow checks — high-precision-low-recall by design. The full
RFC-V validator would need a LaTeX-aware parser; v0.1 catches the
unambiguous-violation patterns and reports per-document label coverage.

Coverage:
  RFCV.S2.regimes  - lowercase-regime discipline (`$c$`/`$s$`/`$r$` not
                     `$C$`/`$S$`/`$R$` when used as regime labels in prose).
  RFCV.S4.compress - $C$ used adjacent to compression-context vocabulary
                     (likely should be $\\mathcal{C}$ per §4 disambiguation).
  RFCV.S4.epsilon  - $\\varepsilon$ without subscript near level/ascent
                     vocabulary (RFC-V §4 requires subscript when level ≠ 0).

Output also includes an INFO-severity registry-coverage report: which
RFC-V §2 cross-cutting labels appear in the document.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .diagnostics import Diagnostic, Severity

# RFC-V §2 cross-cutting label registry (string-form, for coverage scan).
RFCV_REGISTRY = {
    "operators": [r"\$C\$", r"\$S\$", r"\$K\$", r"\$R\$", r"\\mathcal\{C\}"],
    "regimes": [r"\$c\$", r"\$s\$", r"\$r\$", r"k_\{?\\text\{frust\}?\}?"],
    "universality": [r"X_c", r"alpha_s", r"\\alpha_s", r"P_s", r"X_r", r"N_f"],
    "intents": [r"\bI[1-5]\b"],
    "compression": [r"\\epsilon\b", r"\\varepsilon", r"\\mathcal\{C\}_n", r"\\rho\b", r"\\mathcal\{T\}"],
}

COMPRESS_CONTEXT = re.compile(
    r"\b(compression|compress(?:es|ing|ed)|tower|RG[- ]?flow|Banach|operator[- ]?norm|"
    r"contraction|Wilson|Kadanoff|coarse[- ]?grain)\b",
    re.IGNORECASE,
)
LEVEL_CONTEXT = re.compile(
    r"\b(level|ascent|tower|level-?n|n-th|nth)\b",
    re.IGNORECASE,
)
PROSE_REGIME_UPPERCASE = re.compile(
    r"\bregime\s+\$?([CSR])\$?\b"  # "regime C", "regime $C$" — should be lowercase
)
LONE_C_GLYPH = re.compile(r"(?<!\\mathcal\{)\$C\$")  # $C$ not preceded by \mathcal{
LONE_VAREPSILON = re.compile(r"\\varepsilon(?![_{])")  # \varepsilon without _ or {


def check_text(text: str, source: str = "") -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    diags.extend(_check_regime_uppercase(text, source))
    diags.extend(_check_compress_glyph(text, source))
    diags.extend(_check_varepsilon_subscript(text, source))
    diags.extend(_registry_coverage(text, source))
    return diags


def check_file(path: str | Path) -> list[Diagnostic]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    return check_text(text, source=str(p))


def _line_no(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def _check_regime_uppercase(text: str, src: str) -> Iterable[Diagnostic]:
    for m in PROSE_REGIME_UPPERCASE.finditer(text):
        ln = _line_no(text, m.start())
        glyph = m.group(1)
        yield Diagnostic(
            "RFCV.S2.regimes", Severity.WARNING,
            f"'regime {glyph}' uses uppercase glyph; RFC-V §2 canonicalizes regimes as lowercase $c$/$s$/$r$",
            src, f"line {ln}",
        )


def _check_compress_glyph(text: str, src: str) -> Iterable[Diagnostic]:
    for m in LONE_C_GLYPH.finditer(text):
        # Look ±200 chars for compression-context vocabulary
        window = text[max(0, m.start() - 200): m.end() + 200]
        if COMPRESS_CONTEXT.search(window):
            ln = _line_no(text, m.start())
            yield Diagnostic(
                "RFCV.S4.compress", Severity.WARNING,
                "'$C$' near compression-context vocabulary may collide with the try-merge operator; "
                "RFC-V §4 reserves $\\mathcal{C}$ for the compression operator",
                src, f"line {ln}",
            )


def _check_varepsilon_subscript(text: str, src: str) -> Iterable[Diagnostic]:
    for m in LONE_VAREPSILON.finditer(text):
        window = text[max(0, m.start() - 200): m.end() + 200]
        if LEVEL_CONTEXT.search(window):
            ln = _line_no(text, m.start())
            yield Diagnostic(
                "RFCV.S4.epsilon", Severity.WARNING,
                r"'\varepsilon' without subscript near level/ascent context; RFC-V §4 requires subscript when level ≠ 0",
                src, f"line {ln}",
            )


def _registry_coverage(text: str, src: str) -> Iterable[Diagnostic]:
    found: list[str] = []
    for category, patterns in RFCV_REGISTRY.items():
        hits = []
        for p in patterns:
            if re.search(p, text):
                hits.append(p)
        if hits:
            found.append(f"{category}: {len(hits)}/{len(patterns)}")
    if found:
        yield Diagnostic(
            "RFCV.COVERAGE", Severity.INFO,
            "RFC-V §2 label coverage — " + "; ".join(found),
            src,
        )
