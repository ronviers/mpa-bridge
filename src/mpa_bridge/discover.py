"""Component 5: driver discoverer (DBS-backward).

Given a data description, rank available drivers by gamut + operating-envelope
compatibility. Output is a ranked list with per-driver coverage summary.

Same shape as component 6: read all reference drivers as system context,
ask Haiku to score the match. Cheap, fast, gradeable from the cache.
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import assist

ATLAS = Path(r"H:\mpa-atlas")
REFERENCE_DRIVERS = ATLAS / "reference-drivers"

SYSTEM_PROMPT = """You are the driver discoverer for mpa-bridge.

Given data of unknown / partially-known substrate provenance, rank the
available drivers by compatibility. For each candidate driver evaluate:

1. **Gamut coverage** (RFC-S §4 `gamut`). Does the driver's D-range,
   tau_obs range Π(S), trail-class support, shear-profile envelope, and
   persistence depth N(S) cover the data's apparent operating point?
2. **Operating-envelope match** (RFC-S §4 `operating_envelope`). Are the
   driver's calibration prerequisites (initial conditions, parameter
   ranges, measurement protocol) plausibly met by the data?
3. **Match score 0–100** with a one-line rationale.

Output format:

```
## <driver name>
- score: <0-100>
- gamut: <covers / partial / does-not-cover, with the gap named>
- envelope: <calibration prerequisites met / unmet, with what's missing>
- rationale: <one line>
```

If no driver covers the data, say so explicitly and suggest using
`mpa-bridge gap-report` for a characterization-gap analysis.

Reference drivers follow."""


def run(data_path: str | None = None) -> int:
    if not data_path:
        print("usage: mpa-bridge discover <data-description-file>", file=sys.stderr)
        return 2

    p = Path(data_path)
    if not p.exists():
        print(f"error: file not found: {data_path}", file=sys.stderr)
        return 2

    data_text = p.read_text(encoding="utf-8")
    drivers = sorted(REFERENCE_DRIVERS.glob("*.md"))
    drivers_text = "\n\n---\n\n".join(
        f"### {d.name}\n\n{d.read_text(encoding='utf-8')}" for d in drivers
    )

    system = f"{SYSTEM_PROMPT}\n\n{drivers_text}"
    prompt = (
        f"Data description (from {p.name}):\n\n{data_text}\n\n"
        "Rank the drivers."
    )

    ranking = assist.ask(prompt, system=system, model=assist.HAIKU, max_tokens=2048)
    print(ranking)
    return 0
