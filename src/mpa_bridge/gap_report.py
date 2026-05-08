"""Component 6: characterization-gap reporter (DBS-backward) — STUB.

Plan: pointed at data with no compatible driver, declare what would be needed
rather than fail generically.
  - Scan v9 §Substrate-conditional reading rules + reference-drivers/ for
    the closest substrate class.
  - Declare missing characterization fields (no D-range estimate; no τ_obs
    range; no shear-profile envelope; etc.).
  - Suggest a characterization protocol from the closest reference driver.

This is the *informed silence* the Block-In §3 DBS bidirectionality describes.
The tool is the operational vehicle for the principle's backward direction.

Blocked on: the same registry as component 5, plus a small read-only loader
for v9 §Substrate-conditional reading rules. The loader is the only place
where the tool reads v9 directly (every other component reads driver
profiles, not v9).
"""


def run() -> int:
    print("BRIDGE.STUB: gap-report (component 6) is not implemented in v0.1.")
    print("Plan-of-record: handoff_protocol-tool.md §6 'Characterization-gap reporter (DBS-backward)'.")
    return 1
