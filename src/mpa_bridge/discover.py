"""Component 5: driver discoverer (DBS-backward) — STUB.

Plan: pointed at unknown / partially-known data, iterate available driver
profiles to find compatible ones. For each candidate driver:
  - Check `gamut` envelope coverage.
  - Check `operating_envelope` calibration prerequisites.
  - Score match.
Returns a ranked list of candidate drivers + per-driver coverage summary.

Blocked on: a registry of available driver profiles (currently only the
surface-code reference exists; a second reference at habit-extinction is the
v0.2 trigger per the handoff).
"""


def run() -> int:
    print("BRIDGE.STUB: discover (component 5) is not implemented in v0.1.")
    print("Plan-of-record: handoff_protocol-tool.md §5 'Driver discoverer (DBS-backward)'.")
    return 1
