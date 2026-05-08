"""Component 6: characterization-gap reporter (DBS-backward).

Pointed at data with no compatible driver, declare what would be needed
rather than fail generically. Reads:
  - v9 §Substrate-conditional reading rules (rigor source)
  - reference-drivers/ (the closest-substrate-class candidates)
  - the user-supplied data description

Asks Haiku for a structured gap report. Output names: closest substrate
class, missing characterization fields, suggested protocol from the closest
reference driver. This is the *informed silence* the Block-In §3 DBS
bidirectionality describes.
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import assist

ATLAS = Path(r"H:\mpa-atlas")
V9 = ATLAS / "framework" / "v9_compressed.md"
REFERENCE_DRIVERS = ATLAS / "reference-drivers"

SYSTEM_PROMPT = """You are the characterization-gap reporter for mpa-bridge.

mpa-atlas is a protocol framework for substrate-neutral specifications of
dynamical structure. Drivers translate between substrate-native data and the
canonical representation v9 defines. When data arrives without a compatible
driver, your job is to characterize the gap, not reject the data.

Output a structured report with three sections:

1. **Closest substrate class.** Name the reference driver whose gamut /
   reading rules best fit the data. If multiple are plausible, rank them.
2. **Missing characterization fields.** Per RFC-S §4 driver-profile shape:
   D-range, tau_obs range Π(S), shear-profile envelope, trail-class support,
   persistence depth N(S), contraction-rate fit. Name the ones the data does
   not yet pin down.
3. **Suggested protocol.** Adapt the closest reference driver's
   `operating_envelope.measurement_protocol` to the new substrate. Be
   concrete — name what to measure and how.

Reference materials follow."""


def run(data_path: str | None = None) -> int:
    if not data_path:
        print("usage: mpa-bridge gap-report <data-description-file>", file=sys.stderr)
        return 2

    p = Path(data_path)
    if not p.exists():
        print(f"error: file not found: {data_path}", file=sys.stderr)
        return 2

    data_text = p.read_text(encoding="utf-8")
    v9_text = V9.read_text(encoding="utf-8")
    drivers = sorted(REFERENCE_DRIVERS.glob("*.md"))
    drivers_text = "\n\n---\n\n".join(
        f"### {d.name}\n\n{d.read_text(encoding='utf-8')}" for d in drivers
    )

    system = (
        f"{SYSTEM_PROMPT}\n\n"
        f"## v9 (compressed, operational)\n\n{v9_text}\n\n"
        f"## reference drivers\n\n{drivers_text}"
    )
    prompt = (
        f"Data description (from {p.name}):\n\n{data_text}\n\n"
        "Produce the gap report."
    )

    report = assist.ask(prompt, system=system, model=assist.HAIKU, max_tokens=4096)
    print(report)
    return 0
