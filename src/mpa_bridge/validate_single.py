"""Component 1: single-artifact validator.

Runs RFC §3 invariants that are computable from one artifact alone.
Cross-artifact predicates live in component 2 (validate_constellation).

Coverage targets:
  RFC-1 §3 inv. 1 (type-closure), 3 (observer-relativity), 5 (capacity, when
                  numerically computable), 6 (tower-convergence), 7 (demand).
                  inv. 2 (sign-canonicity) is trust-based at the spec layer
                  (no mechanical distinguisher); inv. 4 (scale-monotonicity)
                  needs band_keying — checked when present, skipped otherwise.
  RFC-2 §3 inv. 1 (regime/object), 2 (universality-tuple completeness),
                  4 (observer-relativity), 6 (sampling adequacy: presence),
                  7 (domain bounds).
  RFC-S §4       required sections + header subfields + non-empty
                  reference_outputs.
  RFC-RI §3      shape (spec_ref, intent, canonical_snapshot, signature_targets,
                  acceptance, realizer_class_target). Inv. 4 (cross-artifact)
                  defers to component 2.
"""

from __future__ import annotations

import math
from typing import Any, Iterable

from .diagnostics import Diagnostic, Severity

VALID_REGIMES_VERTEX = {"c", "s", "r", "*"}
VALID_REGIMES_SIG = {"c", "s", "r", "k_frust"}
VALID_SUBGRAPH_FLAGS = {"prescribed_frust", "forbidden_frust", "unspecified"}
VALID_INTENTS = {"I1", "I2", "I3", "I4", "I5"}
REQUIRED_DRIVER_SECTIONS = {
    "header",
    "operating_envelope",
    "gamut",
    "translation_field",
    "intents",
    "reference_outputs",
    "metadata",
}
REQUIRED_DRIVER_HEADER_FIELDS = {
    "profile_version",
    "target_rfc_versions",
    "substrate_class",
    "characterization_date",
    "authority",
    "validation_history",
}


def validate(doc: dict[str, Any], kind: str, source: str = "") -> list[Diagnostic]:
    if kind == "spec":
        return list(_validate_spec(doc, source))
    if kind == "signature":
        return list(_validate_signature(doc, source))
    if kind == "driver_profile":
        return list(_validate_driver_profile(doc, source))
    if kind == "r_doc":
        return list(_validate_r_doc(doc, source))
    return [
        Diagnostic(
            code="BRIDGE.UNKNOWN_ARTIFACT",
            severity=Severity.ERROR,
            message=f"could not identify artifact kind",
            artifact=source,
        )
    ]


# --- spec object (RFC-1) -----------------------------------------------------


def _spec_field(doc: dict, *names: str) -> Any:
    for n in names:
        if n in doc:
            return doc[n]
    return None


def _validate_spec(doc: dict, src: str) -> Iterable[Diagnostic]:
    yield from _spec_inv1_type_closure(doc, src)
    yield from _spec_inv3_observer(doc, src)
    yield from _spec_inv5_capacity(doc, src)
    yield from _spec_inv6_tower(doc, src)
    yield from _spec_inv7_demand(doc, src)


def _spec_inv1_type_closure(doc: dict, src: str) -> Iterable[Diagnostic]:
    vertices = _spec_field(doc, "V", "vertices") or []
    for i, v in enumerate(vertices):
        regime = (v or {}).get("regime_target")
        if regime is None:
            yield Diagnostic(
                "RFC1.INV.1", Severity.ERROR,
                "vertex missing regime_target",
                src, f"V[{i}]",
            )
        elif regime not in VALID_REGIMES_VERTEX:
            yield Diagnostic(
                "RFC1.INV.1", Severity.ERROR,
                f"regime_target {regime!r} not in {{c, s, r, *}}",
                src, f"V[{i}].regime_target",
            )

    subgraphs = doc.get("Gamma") or doc.get("subgraphs") or []
    for i, g in enumerate(subgraphs):
        flag = (g or {}).get("flag")
        if flag is None:
            yield Diagnostic(
                "RFC1.INV.1", Severity.ERROR,
                "subgraph missing flag",
                src, f"Gamma[{i}]",
            )
        elif flag not in VALID_SUBGRAPH_FLAGS:
            yield Diagnostic(
                "RFC1.INV.1", Severity.ERROR,
                f"subgraph flag {flag!r} not in {{prescribed_frust, forbidden_frust, unspecified}}",
                src, f"Gamma[{i}].flag",
            )


def _spec_inv3_observer(doc: dict, src: str) -> Iterable[Diagnostic]:
    tau = doc.get("tau_obs")
    if tau is None:
        yield Diagnostic(
            "RFC1.INV.3", Severity.ERROR,
            "tau_obs missing — observer kernel must be declared",
            src, "tau_obs",
        )
        return
    if isinstance(tau, dict) and "form" in tau:
        if tau["form"] not in {"point", "band", "multi_band", "multi-band"}:
            yield Diagnostic(
                "RFC1.INV.3", Severity.ERROR,
                f"tau_obs.form {tau['form']!r} not in {{point, band, multi_band}}",
                src, "tau_obs.form",
            )


def _spec_inv5_capacity(doc: dict, src: str) -> Iterable[Diagnostic]:
    """Per declared subgraph: |members| ≤ √(2D / α γ_min d_avg)."""
    drive = doc.get("D")
    D_value = _drive_point_value(drive)
    if D_value is None:
        yield Diagnostic(
            "RFC1.INV.5", Severity.INFO,
            "capacity check skipped: D is not point-form numeric",
            src, "D",
        )
        return

    edges = _spec_field(doc, "E", "edges") or []
    shear_values = []
    for e in edges:
        s = (e or {}).get("shear")
        if isinstance(s, (int, float)) and s != 0:
            shear_values.append(abs(float(s)))
    if not shear_values:
        yield Diagnostic(
            "RFC1.INV.5", Severity.INFO,
            "capacity check skipped: no numeric edge shears available",
            src, "E",
        )
        return
    gamma_min = min(shear_values)

    vertices = _spec_field(doc, "V", "vertices") or []
    n_vertices = len(vertices)
    if n_vertices == 0:
        return
    d_avg = (2 * len(edges)) / n_vertices  # 2|E| / |V|, undirected
    if d_avg <= 0:
        return

    alpha = float(doc.get("alpha", 1.0))
    bound = math.sqrt(2.0 * D_value / (alpha * gamma_min * d_avg))

    subgraphs = doc.get("Gamma") or doc.get("subgraphs") or []
    for i, g in enumerate(subgraphs):
        flag = (g or {}).get("flag")
        members = (g or {}).get("members") or []
        if flag == "prescribed_frust" and len(members) > bound:
            yield Diagnostic(
                "RFC1.INV.5", Severity.ERROR,
                f"prescribed subgraph size {len(members)} exceeds capacity bound "
                f"{bound:.3g} at D={D_value} (α={alpha}, γ_min={gamma_min}, d_avg={d_avg:.3g})",
                src, f"Gamma[{i}]",
            )


def _drive_point_value(drive: Any) -> float | None:
    if isinstance(drive, (int, float)):
        return float(drive)
    if isinstance(drive, dict):
        if drive.get("form") == "point" and isinstance(drive.get("value"), (int, float)):
            return float(drive["value"])
    return None


def _spec_inv6_tower(doc: dict, src: str) -> Iterable[Diagnostic]:
    persistence = doc.get("P") or doc.get("persistence") or {}
    tower = persistence.get("tower") if isinstance(persistence, dict) else None
    if not tower:
        return
    for n, level in enumerate(tower):
        if not isinstance(level, dict):
            continue
        eps = level.get("ε_n", level.get("epsilon_n", level.get("eps_n")))
        wall = level.get("complexity_wall", False)
        if eps is None and not wall:
            yield Diagnostic(
                "RFC1.INV.6", Severity.ERROR,
                f"persistence level n={n} missing ε_n and no complexity_wall declared",
                src, f"P.tower[{n}]",
            )
            continue
        if isinstance(eps, (int, float)) and eps >= 1.0 and not wall:
            yield Diagnostic(
                "RFC1.INV.6", Severity.ERROR,
                f"ε_n={eps} ≥ 1 at level {n}; tower fails to converge and no complexity_wall declared",
                src, f"P.tower[{n}].ε_n",
            )


def _spec_inv7_demand(doc: dict, src: str) -> Iterable[Diagnostic]:
    demand = doc.get("demand_envelope") or doc.get("demand")
    if not demand:
        yield Diagnostic(
            "RFC1.INV.7", Severity.ERROR,
            "demand envelope missing or empty — every spec must declare per-object demand",
            src, "demand_envelope",
        )
        return
    if isinstance(demand, dict):
        per_object = demand.get("per_object") or []
    elif isinstance(demand, list):
        per_object = demand
    else:
        per_object = []
    if not per_object:
        yield Diagnostic(
            "RFC1.INV.7", Severity.ERROR,
            "demand envelope has no per_object entries",
            src, "demand_envelope.per_object",
        )


# --- FDR signature (RFC-2) ---------------------------------------------------


def _validate_signature(doc: dict, src: str) -> Iterable[Diagnostic]:
    regime = doc.get("regime_class")
    if regime not in VALID_REGIMES_SIG:
        yield Diagnostic(
            "RFC2.INV.1", Severity.ERROR,
            f"regime_class {regime!r} not in {{c, s, r, k_frust}}",
            src, "regime_class",
        )
        # continue: other checks may still be informative

    if "object_ref" not in doc:
        yield Diagnostic(
            "RFC2.INV.1", Severity.ERROR,
            "object_ref missing",
            src, "object_ref",
        )

    yield from _sig_inv2_universality(doc, src, regime)
    yield from _sig_inv4_observer(doc, src)
    yield from _sig_inv6_sampling(doc, src)
    yield from _sig_inv7_domain(doc, src)


def _sig_inv2_universality(doc: dict, src: str, regime: Any) -> Iterable[Diagnostic]:
    tup = doc.get("universality_tuple") or {}
    required_by_regime = {
        "c": ["X_c"],
        "s": ["alpha_s", "P_s"],
        "r": ["X_r"],
        "k_frust": ["N_f"],
    }
    needed = required_by_regime.get(regime, [])
    for f in needed:
        if f not in tup:
            yield Diagnostic(
                "RFC2.INV.2", Severity.ERROR,
                f"universality_tuple missing {f!r} required for regime {regime!r}",
                src, f"universality_tuple.{f}",
            )


def _sig_inv4_observer(doc: dict, src: str) -> Iterable[Diagnostic]:
    if "observer_kernel" not in doc:
        yield Diagnostic(
            "RFC2.INV.4", Severity.ERROR,
            "observer_kernel missing",
            src, "observer_kernel",
        )


def _sig_inv6_sampling(doc: dict, src: str) -> Iterable[Diagnostic]:
    plot = doc.get("parametric_plot") or {}
    samples = plot.get("samples") if isinstance(plot, dict) else None
    if not samples:
        yield Diagnostic(
            "RFC2.INV.6", Severity.ERROR,
            "parametric_plot.samples missing or empty",
            src, "parametric_plot.samples",
        )


def _sig_inv7_domain(doc: dict, src: str) -> Iterable[Diagnostic]:
    tup = doc.get("universality_tuple") or {}
    bounds = {
        "X_c": (0.0, 1.0),
        "X_r": (0.0, 1.0),
        "P_s": (0.0, 1.0),
        "N_f": (-1.0, 0.0),
    }
    for field, (lo, hi) in bounds.items():
        v = tup.get(field)
        if isinstance(v, (int, float)) and not (lo <= float(v) <= hi):
            yield Diagnostic(
                "RFC2.INV.7", Severity.ERROR,
                f"{field}={v} out of [{lo}, {hi}]",
                src, f"universality_tuple.{field}",
            )


# --- realizer-interface document (RFC-RI) ------------------------------------


def _validate_r_doc(doc: dict, src: str) -> Iterable[Diagnostic]:
    if not doc.get("spec_ref"):
        yield Diagnostic(
            "RFC-RI.INV.1", Severity.ERROR,
            "spec_ref missing",
            src, "spec_ref",
        )
    intent = doc.get("intent")
    if intent not in VALID_INTENTS:
        yield Diagnostic(
            "RFC-RI.SHAPE", Severity.ERROR,
            f"intent {intent!r} not in {{I1..I5}}",
            src, "intent",
        )
    if "canonical_snapshot" not in doc:
        yield Diagnostic(
            "RFC-RI.SHAPE", Severity.ERROR,
            "canonical_snapshot missing",
            src, "canonical_snapshot",
        )
    targets = doc.get("signature_targets") or []
    if not targets:
        yield Diagnostic(
            "RFC-RI.SHAPE", Severity.ERROR,
            "signature_targets missing or empty",
            src, "signature_targets",
        )
    acceptance = doc.get("acceptance") or {}
    if not isinstance(acceptance, dict):
        yield Diagnostic(
            "RFC-RI.INV.3", Severity.ERROR,
            "acceptance must be an object with forward + round-trip thresholds",
            src, "acceptance",
        )
    else:
        for needed in ("forward_threshold", "round_trip_threshold"):
            if needed not in acceptance:
                yield Diagnostic(
                    "RFC-RI.INV.3", Severity.ERROR,
                    f"acceptance.{needed} missing",
                    src, f"acceptance.{needed}",
                )
    if not doc.get("realizer_class_target"):
        yield Diagnostic(
            "RFC-RI.SHAPE", Severity.ERROR,
            "realizer_class_target missing",
            src, "realizer_class_target",
        )


# --- driver profile (RFC-S §4) ----------------------------------------------


def _validate_driver_profile(doc: dict, src: str) -> Iterable[Diagnostic]:
    missing = REQUIRED_DRIVER_SECTIONS - set(doc.keys())
    for section in sorted(missing):
        yield Diagnostic(
            "RFC-S.SEC", Severity.ERROR,
            f"required driver-profile section {section!r} missing",
            src, section,
        )

    header = doc.get("header") or {}
    if isinstance(header, dict):
        missing_h = REQUIRED_DRIVER_HEADER_FIELDS - set(header.keys())
        for f in sorted(missing_h):
            yield Diagnostic(
                "RFC-S.HEADER", Severity.ERROR,
                f"header field {f!r} missing",
                src, f"header.{f}",
            )

    refs = doc.get("reference_outputs") or []
    if not refs:
        yield Diagnostic(
            "RFC-S.REF", Severity.ERROR,
            "reference_outputs missing or empty — round-trip validation requires at least one reference dataset",
            src, "reference_outputs",
        )

    intents = doc.get("intents") or {}
    if isinstance(intents, dict):
        for name, body in intents.items():
            if name not in VALID_INTENTS:
                yield Diagnostic(
                    "RFC-S.INTENT", Severity.WARNING,
                    f"intent key {name!r} not in {{I1..I5}}",
                    src, f"intents.{name}",
                )
                continue
            if not isinstance(body, dict):
                continue
            if "supported" not in body:
                yield Diagnostic(
                    "RFC-S.INTENT", Severity.ERROR,
                    f"intent {name} missing 'supported' field",
                    src, f"intents.{name}.supported",
                )
