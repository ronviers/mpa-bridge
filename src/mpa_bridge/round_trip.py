"""Component 4: round-trip checker — STUB.

Plan: R_doc × measured signatures → diagnostics. Reads the substrate's
actually-produced FDR signatures and compares against R_doc.signature_targets
per the intent's metric (RFC-S §5). Outputs forward-error and round-trip-error
per signature; flags any threshold violation.

Blocked on: surface-code reference dataset (or any other reference driver).
"""


def run() -> int:
    print("BRIDGE.STUB: round-trip (component 4) is not implemented in v0.1.")
    print("Plan-of-record: handoff_protocol-tool.md §4 'Round-trip checker'.")
    return 1
