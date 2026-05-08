"""Component 3: compiler — STUB.

Plan: spec object × intent → R_doc per RFC-1 §4 + RFC-RI.
  1. Validate the spec (component 1).
  2. Project the canonical representation through the intent's mapping
     operation per RFC-S §3 (e.g., scale-uniform under I1).
  3. Generate signature_targets per spec-object element, anchoring on the
     relevant driver profile's reference_outputs.
  4. Set acceptance thresholds per RFC-S §5 metric.
  5. Emit the R_doc (RFC-RI shape).

Blocked on: schema files (handoff_schema_files.md) for canonical-snapshot
field shape; surface-code reference driver's intent operation tables.
"""


def run() -> int:
    print("BRIDGE.STUB: compile (component 3) is not implemented in v0.1.")
    print("Plan-of-record: handoff_protocol-tool.md §3 'Compiler'.")
    return 1
