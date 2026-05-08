"""Component 2: constellation validator.

Implements RFC-3 §3 (C-rules) + §4 (K-rules). Each predicate is computable
from the artifact contents alone — no human judgment.

Constellation = {spec, driver_profile, r_doc, signatures?}.
Per-artifact validity (each RFC's §3) is checked first; cross-artifact
predicates run only if all four artifacts loaded.
"""

from __future__ import annotations

from typing import Any, Iterable

from .diagnostics import Diagnostic, Severity
from .validate_single import validate as validate_one


def validate(
    spec: dict[str, Any] | None,
    driver: dict[str, Any] | None,
    r_doc: dict[str, Any] | None,
    signatures: list[dict[str, Any]] | None = None,
    sources: dict[str, str] | None = None,
) -> list[Diagnostic]:
    src = sources or {}
    diags: list[Diagnostic] = []

    # RFC-3 §5 inv. 1: independent validity per each RFC's §3.
    if spec is not None:
        diags.extend(validate_one(spec, "spec", src.get("spec", "spec")))
    if driver is not None:
        diags.extend(validate_one(driver, "driver_profile", src.get("driver", "driver")))
    if r_doc is not None:
        diags.extend(validate_one(r_doc, "r_doc", src.get("r_doc", "r_doc")))
    for i, sig in enumerate(signatures or []):
        diags.extend(validate_one(sig, "signature", src.get(f"signature[{i}]", f"signature[{i}]")))

    if spec is None or driver is None or r_doc is None:
        diags.append(Diagnostic(
            "RFC3.PARTIAL", Severity.INFO,
            "constellation incomplete (need spec, driver, r_doc); only independent validity reported",
        ))
        return diags

    # Cross-artifact predicates.
    diags.extend(_c1_gamut_ranges(spec, driver))
    diags.extend(_c2_trail_class_support(spec, driver))
    diags.extend(_c3_intent_supported(r_doc, driver))
    diags.extend(_c4_realizer_class(r_doc, driver))
    diags.extend(_c5_persistence_depth(spec, driver))
    diags.extend(_k1_signature_target_completeness(spec, r_doc))

    return diags


# --- C-rules ----------------------------------------------------------------


def _c1_gamut_ranges(spec: dict, driver: dict) -> Iterable[Diagnostic]:
    """C1: spec's (τ_obs, D) ⊆ driver's gamut ranges."""
    gamut = driver.get("gamut") or {}

    spec_D = _drive_point_value_simple(spec.get("D"))
    D_range = _range_pair(gamut.get("D_range") or gamut.get("D-range"))
    if spec_D is not None and D_range is not None:
        lo, hi = D_range
        if not (lo <= spec_D <= hi):
            yield Diagnostic(
                "RFC3.C1", Severity.ERROR,
                f"spec D={spec_D} outside driver gamut D-range [{lo}, {hi}]",
                "constellation", "spec.D",
            )

    spec_tau = _tau_point_value(spec.get("tau_obs"))
    tau_range = _range_pair(gamut.get("tau_obs_range") or gamut.get("Π(S)"))
    if spec_tau is not None and tau_range is not None:
        lo, hi = tau_range
        if not (lo <= spec_tau <= hi):
            yield Diagnostic(
                "RFC3.C1", Severity.ERROR,
                f"spec tau_obs={spec_tau} outside driver gamut Π(S) [{lo}, {hi}]",
                "constellation", "spec.tau_obs",
            )


def _c2_trail_class_support(spec: dict, driver: dict) -> Iterable[Diagnostic]:
    """C2: spec's V/E/Γ types ∈ driver's gamut.trail_class_support."""
    support = (driver.get("gamut") or {}).get("trail_class_support")
    if support is None:
        yield Diagnostic(
            "RFC3.C2", Severity.INFO,
            "driver gamut.trail_class_support not declared; C2 cannot evaluate",
            "constellation", "driver.gamut.trail_class_support",
        )
        return
    if not isinstance(support, (list, set)):
        return
    support_set = set(support)
    vertices = spec.get("V") or spec.get("vertices") or []
    for i, v in enumerate(vertices):
        tv_type = (v or {}).get("trail_vector_type")
        if tv_type is not None and tv_type not in support_set:
            yield Diagnostic(
                "RFC3.C2", Severity.ERROR,
                f"vertex trail_vector_type {tv_type!r} not in driver trail_class_support {sorted(support_set)}",
                "constellation", f"spec.V[{i}].trail_vector_type",
            )


def _c3_intent_supported(r_doc: dict, driver: dict) -> Iterable[Diagnostic]:
    """C3: R_doc's intent ∈ driver's supported intents."""
    intent = r_doc.get("intent")
    intents = driver.get("intents") or {}
    if intent not in intents:
        yield Diagnostic(
            "RFC3.C3", Severity.ERROR,
            f"R_doc.intent={intent!r} not present in driver.intents (declared: {sorted(intents) if isinstance(intents, dict) else intents!r})",
            "constellation", "r_doc.intent",
        )
        return
    body = intents[intent] if isinstance(intents, dict) else None
    if isinstance(body, dict) and body.get("supported") is False:
        yield Diagnostic(
            "RFC3.C3", Severity.ERROR,
            f"driver does not support intent {intent}",
            "constellation", f"driver.intents.{intent}.supported",
        )


def _c4_realizer_class(r_doc: dict, driver: dict) -> Iterable[Diagnostic]:
    """C4: R_doc's realizer_class_target = driver's substrate_class."""
    target = r_doc.get("realizer_class_target")
    sub_class = (driver.get("header") or {}).get("substrate_class")
    if target and sub_class and target != sub_class:
        yield Diagnostic(
            "RFC3.C4", Severity.ERROR,
            f"R_doc.realizer_class_target={target!r} ≠ driver.substrate_class={sub_class!r}",
            "constellation", "r_doc.realizer_class_target",
        )


def _c5_persistence_depth(spec: dict, driver: dict) -> Iterable[Diagnostic]:
    """C5: spec persistence depth N ≤ driver's gamut.persistence_depth N(S)."""
    persistence = spec.get("P") or spec.get("persistence") or {}
    tower = persistence.get("tower") if isinstance(persistence, dict) else None
    if not tower:
        return
    spec_N = len(tower)
    gamut = driver.get("gamut") or {}
    driver_N = gamut.get("persistence_depth") or gamut.get("N(S)")
    if isinstance(driver_N, (int, float)) and spec_N > driver_N:
        yield Diagnostic(
            "RFC3.C5", Severity.ERROR,
            f"spec persistence depth N={spec_N} exceeds driver N(S)={driver_N}",
            "constellation", "spec.P.tower",
        )


# --- K-rules ----------------------------------------------------------------


def _k1_signature_target_completeness(spec: dict, r_doc: dict) -> Iterable[Diagnostic]:
    """K1: every spec V/E/declared Γ has a signature_targets entry in R_doc."""
    targets = r_doc.get("signature_targets") or []
    target_refs = {(t or {}).get("object_ref") for t in targets if isinstance(t, dict)}
    target_refs.discard(None)

    def _check(elements: list, kind: str, path: str) -> Iterable[Diagnostic]:
        for i, el in enumerate(elements or []):
            el_id = (el or {}).get("id")
            if el_id is None:
                continue
            if el_id not in target_refs:
                yield Diagnostic(
                    "RFC3.K1", Severity.ERROR,
                    f"{kind} {el_id!r} has no signature_targets entry in R_doc",
                    "constellation", f"{path}[{i}].id",
                )

    yield from _check(spec.get("V") or spec.get("vertices") or [], "vertex", "spec.V")
    yield from _check(spec.get("E") or spec.get("edges") or [], "edge", "spec.E")

    declared_subgraphs = [
        g for g in (spec.get("Gamma") or spec.get("subgraphs") or [])
        if isinstance(g, dict) and g.get("flag") in {"prescribed_frust", "forbidden_frust"}
    ]
    yield from _check(declared_subgraphs, "subgraph", "spec.Gamma")


# --- helpers ----------------------------------------------------------------


def _drive_point_value_simple(drive: Any) -> float | None:
    if isinstance(drive, (int, float)):
        return float(drive)
    if isinstance(drive, dict):
        if drive.get("form") == "point" and isinstance(drive.get("value"), (int, float)):
            return float(drive["value"])
    return None


def _tau_point_value(tau: Any) -> float | None:
    if isinstance(tau, (int, float)):
        return float(tau)
    if isinstance(tau, dict):
        if tau.get("form") == "point" and isinstance(tau.get("value"), (int, float)):
            return float(tau["value"])
    return None


def _range_pair(r: Any) -> tuple[float, float] | None:
    if isinstance(r, (list, tuple)) and len(r) == 2:
        if all(isinstance(x, (int, float)) for x in r):
            return float(r[0]), float(r[1])
    if isinstance(r, dict):
        lo, hi = r.get("min"), r.get("max")
        if isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
            return float(lo), float(hi)
    return None
