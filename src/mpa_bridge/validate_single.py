"""Component 1: single-artifact validator.

Two-pass: schema first (delegated to mpa-atlas/schema/ via schema_check),
then §3 invariants that exceed schema (cross-field comparisons, numeric
bounds requiring computation).

What schema covers (no longer duplicated here):
  - Required fields, enum constraints, domain bounds, conditional shape
    (per-regime universality_tuple via if/then), $ref propagation
    (signature_targets are full FDR signatures).

What stays here (§3-extras):
  - RFC-1 inv. 4 scale-monotonicity (cross-band comparison; only when
    band_keying is declared)
  - RFC-1 inv. 5 capacity-respect (numeric: |Γ*| ≤ √(2D / α γ_min d_avg))
  - RFC-1 inv. 6 tower-convergence (ε_n < 1 OR complexity_wall declared)
  - RFC-1 inv. 2 sign-canonicity is trust-based (no mechanical
    distinguisher); skipped.
"""

from __future__ import annotations

import math
from typing import Any, Iterable

from .diagnostics import Diagnostic, Severity
from .schema_check import schema_validate


def validate(doc: dict[str, Any], kind: str, source: str = "") -> list[Diagnostic]:
    if kind not in {"spec", "signature", "driver_profile", "r_doc"}:
        return [
            Diagnostic(
                "BRIDGE.UNKNOWN_ARTIFACT", Severity.ERROR,
                "could not identify artifact kind",
                source,
            )
        ]

    diags = list(schema_validate(doc, kind, source))
    if kind == "spec":
        diags.extend(_spec_invariants_beyond_schema(doc, source))
    return diags


def _spec_invariants_beyond_schema(doc: dict, src: str) -> Iterable[Diagnostic]:
    yield from _spec_inv5_capacity(doc, src)
    yield from _spec_inv6_tower(doc, src)
    # inv. 4 scale-monotonicity needs band_keying on V/E; skip until a multi-band
    # spec lands. Schema admits multi_band shape; this is the cross-band check.


def _spec_inv5_capacity(doc: dict, src: str) -> Iterable[Diagnostic]:
    """Per declared subgraph: |members| ≤ √(2D / α γ_min d_avg).

    Skipped (INFO) when D is not point-form numeric, edges have no numeric
    shears, or no vertices. Capacity is a v9 §Capacity claim about
    sustainable subgraph size at the operating point.
    """
    drive = doc.get("D")
    D_value = _drive_point_value(drive)
    if D_value is None:
        yield Diagnostic(
            "RFC1.INV.5", Severity.INFO,
            "capacity check skipped: D is not point-form numeric",
            src, "D",
        )
        return

    edges = doc.get("E") or doc.get("edges") or []
    shear_values = [
        abs(float(e.get("shear")))
        for e in edges
        if isinstance(e, dict) and isinstance(e.get("shear"), (int, float)) and e.get("shear") != 0
    ]
    if not shear_values:
        yield Diagnostic(
            "RFC1.INV.5", Severity.INFO,
            "capacity check skipped: no numeric edge shears available",
            src, "E",
        )
        return
    gamma_min = min(shear_values)

    vertices = doc.get("V") or doc.get("vertices") or []
    n_vertices = len(vertices)
    if n_vertices == 0:
        return
    d_avg = (2 * len(edges)) / n_vertices
    if d_avg <= 0:
        return

    alpha = float(doc.get("alpha", 1.0))
    bound = math.sqrt(2.0 * D_value / (alpha * gamma_min * d_avg))

    subgraphs = doc.get("Gamma") or doc.get("subgraphs") or []
    for i, g in enumerate(subgraphs):
        if not isinstance(g, dict):
            continue
        if g.get("flag") == "prescribed_frust":
            members = g.get("members") or []
            if len(members) > bound:
                yield Diagnostic(
                    "RFC1.INV.5", Severity.ERROR,
                    f"prescribed subgraph size {len(members)} exceeds capacity bound "
                    f"{bound:.3g} at D={D_value} (α={alpha}, γ_min={gamma_min}, d_avg={d_avg:.3g})",
                    src, f"Gamma[{i}]",
                )


def _spec_inv6_tower(doc: dict, src: str) -> Iterable[Diagnostic]:
    """Each ascent's ε_n < 1 OR a complexity_wall is declared at that level."""
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


def _drive_point_value(drive: Any) -> float | None:
    if isinstance(drive, (int, float)):
        return float(drive)
    if isinstance(drive, dict):
        if drive.get("form") == "point" and isinstance(drive.get("value"), (int, float)):
            return float(drive["value"])
    return None
