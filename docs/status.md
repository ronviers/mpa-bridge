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
| 3 | Compiler (spec × intent → R_doc) | works against surface-code | **working (Sonnet 4.6, validator-gatekept)** | None — Sonnet emits R_doc; component 1 validates the structure; constellation validates against driver. End-to-end round-trip on minimal fixtures: rc=0. |
| 4 | Round-trip checker | works against surface-code | stub | Surface-code reference dataset (real measurement traces, not just the driver profile). |
| 5 | Driver discoverer (DBS-backward) | works against surface-code | **working (Claude-assisted, Haiku 4.5)** | None — produces ranked-list output. Currently only one driver in registry, so "ranking" is trivial; gets meaningful at v0.2 with habit-extinction. |
| 6 | Characterization-gap reporter | works against surface-code | **working (Claude-assisted, Haiku 4.5)** | None — produces structured gap reports against v9 + reference-drivers/. Quality gradeable from `D:\Cache\mpa-bridge\` records. |
| 7 | Vocabulary checker (RFC-V) | end-to-end | working (narrow) | None — narrow checks ship; broader semantic checks need a LaTeX-aware parser. |

**Summary:** components 1, 2, 5, 6, 7 working; component 3 working with validator-gatekeeper pattern (Sonnet emits, deterministic validator certifies). Component 4 (round-trip) remains a stub — it needs a real measurement dataset, not a synthesis surface. Schema files (separate mpa-atlas session) would let component 1 delegate shape-validation to `jsonschema`, but the existing programmatic checks already match each RFC's §2 / §3.

## v0.2 readiness gates

> v0.2 ready when habit-extinction reference driver lands and components 3–6 work cross-substrate.

Not started. Triggered by [`handoff_habit-extinction_reference-driver.md`](https://github.com/ronviers/mpa-atlas/blob/main/architecture/handoff_habit-extinction_reference-driver.md) landing in mpa-atlas.

## Discipline notes

- **Substrate-neutral by construction.** No substrate-specific logic anywhere in `src/mpa_bridge/`. Drivers carry that. Component 6 reads v9 + reference-drivers as system context for Claude; the tool itself encodes none of it.
- **Mechanical-only validation.** Components 1, 2, 4 are strictly deterministic. Same artifact → same diagnostics. The assist surface is forbidden inside validators — that's the load-bearing carve-out for CI to mean anything.
- **DBS-backward via Claude.** Components 3, 5, 6 (compile, discover, gap-report) are the synthesis surfaces. They call `assist.ask` because the framework's commitment to *demand-bounded sufficiency* says the tool produces *some* answer rather than blocking on missing inputs. The cache at `D:\Cache\mpa-bridge\` doubles as a gradable run-log.
- **Diagnostics carry stable codes.** Format: `RFC<n>.INV.<k>` for per-RFC §3 invariants, `RFC3.C<n>` / `RFC3.K<n>` for cross-artifact predicates, `RFCV.S<n>.<tag>` for RFC-V vocabulary checks, `BRIDGE.<TAG>` for tool-internal status. Tests assert on codes; diagnostics are exchange surface with CI.

## Known gaps

- **No JSON Schema validation yet.** When the four schema files (handoff_schema_files.md) land at `mpa-atlas/schema/`, component 1 should delegate shape validation to `jsonschema` and keep §3-invariant predicates as separate post-schema checks. Until then, component 1's shape checks are programmatic re-encodings of each RFC's §2.
- **Spec inv. 4 (scale-monotonicity) only fires on multi-band declarations.** Single-band specs trivially satisfy it; this is a real coverage gap when multi-band specs appear.
- **Spec inv. 2 (sign-canonicity) is trust-based.** No mechanical signal distinguishes a canonical-sign from substrate-native-sign spec; the discipline lives at the driver layer.
- **RFC-V checks are narrow by design.** High-precision-low-recall — three warning rules and a coverage report. Broader checks need a LaTeX-aware parser, not in v0.1 scope.
