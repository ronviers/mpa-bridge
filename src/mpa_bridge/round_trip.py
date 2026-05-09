"""Component 4: round-trip checker (RFC-S §5).

Input: an R_doc and a set of measured FDR signatures (substrate-realized).
Output: per-target forward-error + round-trip-error against R_doc.acceptance,
plus K1-style coverage diagnostics.

v0.1 implements I1 and I5 metrics from the RFC-S §5 table. I2/I3/I4 emit
RFC-S5.METRIC_NA — they need spec/driver context for L^2 drive distance,
|Γ*| deviation, and {ε_n} sequence distance respectively, which v0.1
deliberately defers (real-substrate measurement ergonomics, not tool
mechanics). No realizer here means forward-error and round-trip-error
collapse to the same comparison; the API is shaped for the day a
substrate-specific realizer wires in.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from . import artifacts, validate_single
from .diagnostics import Diagnostic, Severity, has_errors

INTENT_METRIC_TABLE = {
    "I1": "regime-mismatch (Hamming)",
    "I2": "(not implemented in v0.1)",
    "I3": "(not implemented in v0.1)",
    "I4": "(not implemented in v0.1)",
    "I5": "max |Δuniversality_tuple| / categorical regime agreement",
}


def run(rdoc_path: str | None = None, measured_paths: list[str] | None = None) -> int:
    if not rdoc_path or not measured_paths:
        print(
            "usage: mpa-bridge round-trip --rdoc <r_doc.json> "
            "--measured <sig1.json> [<sig2.json> ...]",
            file=sys.stderr,
        )
        return 2

    try:
        rdoc = artifacts.load(rdoc_path)
        measured = [artifacts.load(p) for p in measured_paths]
    except Exception as e:
        print(f"error: failed to load inputs: {e}", file=sys.stderr)
        return 2

    rdoc_diags = validate_single.validate(rdoc, "r_doc", source=rdoc_path)
    if has_errors(rdoc_diags):
        print("error: R_doc is invalid; cannot round-trip.", file=sys.stderr)
        for d in rdoc_diags:
            print(d.format(), file=sys.stderr)
        return 1

    diags = list(_round_trip(rdoc, measured, rdoc_path, measured_paths))
    for d in diags:
        print(d.format())
    return 1 if has_errors(diags) else 0


def _round_trip(
    rdoc: dict, measured: list[dict], rdoc_src: str, measured_srcs: list[str]
) -> Iterable[Diagnostic]:
    intent = rdoc.get("intent")
    targets = rdoc.get("signature_targets") or []
    acceptance = rdoc.get("acceptance") or {}
    fwd_th = acceptance.get("forward_threshold")
    rt_th = acceptance.get("round_trip_threshold")

    tgt_by_ref = {t.get("object_ref"): t for t in targets if isinstance(t, dict)}
    msr_by_ref = {m.get("object_ref"): m for m in measured if isinstance(m, dict)}

    # Coverage: every target needs a measurement.
    for ref in tgt_by_ref:
        if ref not in msr_by_ref:
            yield Diagnostic(
                "RFC-S5.MISSING", Severity.ERROR,
                f"no measurement for target object_ref={ref!r}",
                rdoc_src, f"signature_targets[object_ref={ref}]",
            )

    yield Diagnostic(
        "RFC-S5.INTENT", Severity.INFO,
        f"intent={intent} metric: {INTENT_METRIC_TABLE.get(intent, '(unknown)')}",
        rdoc_src,
    )

    for ref, t in tgt_by_ref.items():
        if ref not in msr_by_ref:
            continue
        m = msr_by_ref[ref]
        forward = _forward_error(t, m, intent)
        if forward is None:
            yield Diagnostic(
                "RFC-S5.METRIC_NA", Severity.INFO,
                f"forward metric for intent {intent} not implemented in v0.1; skipping {ref!r}",
                rdoc_src, ref,
            )
            continue

        if isinstance(fwd_th, (int, float)) and forward > fwd_th:
            yield Diagnostic(
                "RFC-S5.FORWARD", Severity.ERROR,
                f"forward error {forward:.3g} exceeds threshold {fwd_th:.3g} for {ref!r}",
                rdoc_src, ref,
            )
        else:
            yield Diagnostic(
                "RFC-S5.FORWARD", Severity.INFO,
                f"forward error {forward:.3g} ≤ {fwd_th} for {ref!r}",
                rdoc_src, ref,
            )

        # Without a realizer, round-trip-error collapses to forward-error.
        # The acceptance check still runs against the rt threshold so the
        # API surface is shape-compatible with the substrate-realizer day.
        if isinstance(rt_th, (int, float)) and forward > rt_th:
            yield Diagnostic(
                "RFC-S5.ROUND_TRIP", Severity.ERROR,
                f"round-trip error {forward:.3g} exceeds threshold {rt_th:.3g} for {ref!r} "
                f"(no realizer in v0.1; forward = round-trip)",
                rdoc_src, ref,
            )


def _forward_error(target: dict, measured: dict, intent: str | None) -> float | None:
    """Per-intent metric per RFC-S §5. Returns None when not implemented."""
    if intent == "I1":
        # Hamming on regime partition: 1.0 if regime_class differs else 0.0.
        return 0.0 if target.get("regime_class") == measured.get("regime_class") else 1.0

    if intent == "I5":
        # Universality: regime-class disagreement is +inf (different class).
        if target.get("regime_class") != measured.get("regime_class"):
            return float("inf")
        # Within-class parameter distance: max abs diff over shared keys.
        t_tup = target.get("universality_tuple") or {}
        m_tup = measured.get("universality_tuple") or {}
        shared = set(t_tup) & set(m_tup)
        if not shared:
            return 0.0
        return max(
            abs(float(t_tup[k]) - float(m_tup[k]))
            for k in shared
            if isinstance(t_tup.get(k), (int, float)) and isinstance(m_tup.get(k), (int, float))
        )

    return None  # I2, I3, I4 not implemented in v0.1
