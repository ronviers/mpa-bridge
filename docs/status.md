# Status

Tracking against the v0.1 / v0.2 readiness gates declared in [`mpa-atlas/architecture/handoff_protocol-tool.md`](https://github.com/ronviers/mpa-atlas/blob/main/architecture/handoff_protocol-tool.md) §"Completion criteria".

## v0.1 readiness gates

> v0.1 complete when:
> 1. Components 1, 2, 7 work end-to-end against the existing mpa-atlas artifacts.
> 2. Components 3, 4 work against the surface-code reference driver.
> 3. Components 5, 6 work against at least the surface-code reference driver as the only target.

| # | Component | Gate | Status | Blockers |
|---|---|---|---|---|
| 1 | Single-artifact validator | end-to-end against existing artifacts | scaffolded — RFC-1 inv. 1/3/5/6/7, RFC-2 inv. 1/2/4/6/7, RFC-S §4 sections+header, RFC-RI shape | (a) JSON Schema files (per `handoff_schema_files.md`) for full schema-shape validation. (b) An actual published spec / signature / r_doc to validate against. |
| 2 | Constellation validator | end-to-end | scaffolded — RFC-3 C1–C5 + K1 | Same as (1b). |
| 3 | Compiler (spec × intent → R_doc) | works against surface-code | stub | Schemas + canonical-snapshot field shape; surface-code intent operation tables. |
| 4 | Round-trip checker | works against surface-code | stub | Surface-code reference dataset. |
| 5 | Driver discoverer (DBS-backward) | works against surface-code | stub | Driver registry (currently only surface-code; v0.2 trigger is habit-extinction). |
| 6 | Characterization-gap reporter | works against surface-code | stub | Same registry + small read-only loader for v9 §Substrate-conditional reading rules. |
| 7 | Vocabulary checker (RFC-V) | end-to-end | working (narrow) | None — narrow checks ship; broader semantic checks need a LaTeX-aware parser. |

**Summary:** components 1, 2, 7 are scaffolded with mechanical checks running against fixture artifacts. Real-artifact end-to-end blocks on schema files landing in mpa-atlas. Components 3–6 are stubs; their blockers are listed.

## v0.2 readiness gates

> v0.2 ready when habit-extinction reference driver lands and components 3–6 work cross-substrate.

Not started. Triggered by [`handoff_habit-extinction_reference-driver.md`](https://github.com/ronviers/mpa-atlas/blob/main/architecture/handoff_habit-extinction_reference-driver.md) landing in mpa-atlas.

## Discipline notes

- **Substrate-neutral by construction.** No substrate-specific logic anywhere in `src/mpa_bridge/`. Drivers carry that. Component 6 is the lone exception — it reads v9 §Substrate-conditional reading rules to find the closest substrate class for a gap report. Keep that surface narrow.
- **Mechanical-only validation.** Every C# / K# rule is computable from artifact contents. No human judgment.
- **Diagnostics carry stable codes.** Format: `RFC<n>.INV.<k>` for per-RFC §3 invariants, `RFC3.C<n>` / `RFC3.K<n>` for cross-artifact predicates, `RFCV.S<n>.<tag>` for RFC-V vocabulary checks, `BRIDGE.<TAG>` for tool-internal status. Tests assert on codes; diagnostics are exchange surface with CI.

## Known gaps

- **No JSON Schema validation yet.** When the four schema files (handoff_schema_files.md) land at `mpa-atlas/schema/`, component 1 should delegate shape validation to `jsonschema` and keep §3-invariant predicates as separate post-schema checks. Until then, component 1's shape checks are programmatic re-encodings of each RFC's §2.
- **Spec inv. 4 (scale-monotonicity) only fires on multi-band declarations.** Single-band specs trivially satisfy it; this is a real coverage gap when multi-band specs appear.
- **Spec inv. 2 (sign-canonicity) is trust-based.** No mechanical signal distinguishes a canonical-sign from substrate-native-sign spec; the discipline lives at the driver layer.
- **RFC-V checks are narrow by design.** High-precision-low-recall — three warning rules and a coverage report. Broader checks need a LaTeX-aware parser, not in v0.1 scope.
