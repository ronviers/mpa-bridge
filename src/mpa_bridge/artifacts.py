"""Load + identify mpa-atlas exchange artifacts.

Artifact kinds (one per RFC):
  spec            - RFC-1 spec object
  signature       - RFC-2 FDR signature
  driver_profile  - RFC-S §4 driver profile
  r_doc           - RFC-RI realizer-interface document
  unknown         - shape did not match any of the above
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import yaml

ArtifactKind = Literal["spec", "signature", "driver_profile", "r_doc", "unknown"]


def load(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)


def identify(doc: Any) -> ArtifactKind:
    """Return artifact kind based on required-field presence.

    Order is most-specific first. Fields here mirror the §2 Shape table of
    each RFC; alternative naming (e.g., 'vertices' for V) is accepted.
    """
    if not isinstance(doc, dict):
        return "unknown"

    # RFC-RI: realizer-interface document
    if "spec_ref" in doc and "signature_targets" in doc and "intent" in doc:
        return "r_doc"

    # RFC-2: FDR signature
    if "regime_class" in doc and "parametric_plot" in doc:
        return "signature"

    # RFC-S §4: driver profile
    if "header" in doc and "gamut" in doc and "intents" in doc:
        return "driver_profile"

    # RFC-1: spec object. Identification is structural (V/E/D/tau_obs);
    # demand_envelope is a §3 invariant, checked at validation, not identity.
    spec_canonical = {"V", "E", "D", "tau_obs"}
    spec_alt = {"vertices", "edges", "drive", "tau_obs"}
    if spec_canonical.issubset(doc.keys()) or spec_alt.issubset(doc.keys()):
        return "spec"

    return "unknown"
