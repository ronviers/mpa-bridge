"""Component 3: compiler (spec × intent → R_doc).

Validator-as-gatekeeper pattern:
  1. Validate spec via component 1 (early-out if invalid).
  2. Load RFC-1 + RFC-RI + RFC-S + RFC-2 + driver as system context.
  3. Ask Sonnet 4.6 to produce a JSON R_doc matching RFC-RI §2 shape.
  4. Parse the JSON (with a fenced-block fallback for stray markdown).
  5. Validate the R_doc via component 1; surface diagnostics.
  6. Write or print.

Sonnet, not Haiku — structured output where quality matters. The validator
catches structural errors regardless, so the compiler can be loose and the
gatekeeper does the certification.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from . import artifacts, assist, validate_single
from .diagnostics import has_errors

ATLAS = Path(r"H:\mpa-atlas")
RFC_1 = ATLAS / "rfcs" / "MPA-RFC-1_Spec-Object.md"
RFC_RI = ATLAS / "rfcs" / "MPA-RFC-RI_Realizer-Interface.md"
RFC_S = ATLAS / "rfcs" / "MPA-RFC-S_Scale-Management.md"
RFC_2 = ATLAS / "rfcs" / "MPA-RFC-2_FDR-Signatures.md"

SYSTEM_PROMPT = """You are the compiler for mpa-bridge.

Compile an MPA spec object × intent into a realizer-interface document
(R_doc) per RFC-RI §2 shape:

  {
    "spec_ref": <spec id/name>,
    "intent": "I1" | "I2" | "I3" | "I4" | "I5",
    "canonical_snapshot": <spec's canonical representation at its declared
                          tau_obs, projected through the intent's mapping
                          operation per RFC-S §3>,
    "signature_targets": [
      {
        "object_ref": <V/E/Gamma id from spec>,
        "regime_class": "c" | "s" | "r" | "k_frust",
        "parametric_plot": {"samples": [...]},
        "universality_tuple": <regime-conditional fields per RFC-2 §3 inv 2>,
        "observer_kernel": <tau_obs spec>
      },
      ...one entry per spec-object element (V, E, declared Gamma)...
    ],
    "acceptance": {
      "forward_threshold": <number>,
      "round_trip_threshold": <number>
    },
    "realizer_class_target": <must equal driver.header.substrate_class>
  }

Use the intent's mapping operation (RFC-S §3) for canonical_snapshot and
the intent's metric (RFC-S §5) for acceptance thresholds. Anchor
signature_targets on the driver's reference_outputs.

Respond with ONE JSON object only. No markdown fences, no prose, no
commentary. The output will be machine-validated against RFC-RI invariants.

Reference materials follow."""


def run(
    spec_path: str | None = None,
    intent: str | None = None,
    driver_path: str | None = None,
    output_path: str | None = None,
) -> int:
    if not (spec_path and intent and driver_path):
        print(
            "usage: mpa-bridge compile --spec <spec.json> --intent <I1..I5> "
            "--driver <driver.json> [--output <rdoc.json>]",
            file=sys.stderr,
        )
        return 2

    if intent not in {"I1", "I2", "I3", "I4", "I5"}:
        print(f"error: intent {intent!r} not in {{I1..I5}}", file=sys.stderr)
        return 2

    try:
        spec = artifacts.load(spec_path)
        driver = artifacts.load(driver_path)
    except Exception as e:
        print(f"error: failed to load inputs: {e}", file=sys.stderr)
        return 2

    spec_diags = validate_single.validate(spec, "spec", source=spec_path)
    if has_errors(spec_diags):
        print("error: spec is invalid; cannot compile.", file=sys.stderr)
        for d in spec_diags:
            print(d.format(), file=sys.stderr)
        return 1

    rfc_context = "\n\n".join(
        f"## {p.name}\n\n{p.read_text(encoding='utf-8')}"
        for p in (RFC_1, RFC_RI, RFC_S, RFC_2)
    )
    system = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{rfc_context}\n\n"
        f"## driver profile\n\n```json\n{json.dumps(driver, indent=2)}\n```"
    )
    prompt = (
        f"Spec object:\n```json\n{json.dumps(spec, indent=2, ensure_ascii=False)}\n```\n\n"
        f"Intent: {intent}\n\n"
        f"Compile this spec under {intent} against the driver. JSON only."
    )

    response = assist.ask(prompt, system=system, model=assist.SONNET, max_tokens=4096)

    rdoc = _parse_json(response)
    if rdoc is None:
        print("error: compiler response was not valid JSON.", file=sys.stderr)
        print(response, file=sys.stderr)
        return 1

    rdoc_diags = validate_single.validate(rdoc, "r_doc", source="<compiled>")
    for d in rdoc_diags:
        print(d.format(), file=sys.stderr)
    rc = 1 if has_errors(rdoc_diags) else 0

    serialized = json.dumps(rdoc, indent=2, ensure_ascii=False)
    if output_path:
        Path(output_path).write_text(serialized, encoding="utf-8")
        print(f"# wrote R_doc to {output_path}", file=sys.stderr)
    else:
        print(serialized)

    return rc


_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _parse_json(text: str) -> Any | None:
    """Try direct JSON; fall back to extracting from a fenced code block."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _FENCE_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Last resort: first { to last }
    if "{" in text and "}" in text:
        try:
            return json.loads(text[text.index("{"): text.rindex("}") + 1])
        except json.JSONDecodeError:
            pass
    return None
