# Status

Tracking against the v0.1 / v0.2 readiness gates for the seven components (see [README](../README.md) for the component table; [docs/handoff_next_session.md](handoff_next_session.md) for open work).

## v0.1 readiness gates

> v0.1 complete when:
> 1. Components 1, 2, 7 work end-to-end against the existing mpa-atlas artifacts.
> 2. Components 3, 4 work against the surface-code reference driver.
> 3. Components 5, 6 work against at least the surface-code reference driver as the only target.

| # | Component | Gate | Status | Blockers |
|---|---|---|---|---|
| 1 | Single-artifact validator | end-to-end against existing artifacts | **working** — structural shape delegated to mpa-atlas/schema/*.json (Draft 2020-12); §3-extras (capacity, tower-convergence) run after as separate `RFC1.INV.<n>` diagnostics. | None — schemas now exist at `H:\mpa-atlas\schema\` and propagate via `$ref` so RFC-2 required fields surface inside R_doc validation automatically. |
| 2 | Constellation validator | end-to-end | scaffolded — RFC-3 C1–C5 + K1 | Same as (1b). |
| 3 | Compiler (spec × intent → R_doc) | works against surface-code | **working (Sonnet 4.6, validator-gatekept)** | None — Sonnet emits R_doc; component 1 validates the structure; constellation validates against driver. End-to-end round-trip on minimal fixtures: rc=0. |
| 4 | Round-trip checker | works against surface-code | **working (I1 + I5 metrics)** | I2/I3/I4 metrics deferred — they need spec/driver context (L^2 drive distance, \|Γ*\| deviation, {ε_n} sequence distance). Real round-trip-error vs forward-error will diverge once a substrate-realizer is wired. |
| 5 | Driver discoverer (DBS-backward) | works against surface-code | **working (Claude-assisted, Haiku 4.5)** | None — produces ranked-list output. Currently only one driver in registry, so "ranking" is trivial; gets meaningful at v0.2 with habit-extinction. |
| 6 | Characterization-gap reporter | works against surface-code | **working (Claude-assisted, Haiku 4.5)** | None — produces structured gap reports against v9 + reference-drivers/. Quality gradeable from `D:\Cache\mpa-bridge\` records. |
| 7 | Vocabulary checker (RFC-V) | end-to-end | working (narrow) | None — narrow checks ship; broader semantic checks need a LaTeX-aware parser. |

**Summary:** all seven components ship. Components 1, 2, 4, 7 are mechanical (deterministic, suitable for CI). Components 3, 5, 6 are Claude-assisted synthesis surfaces (cache + run-log at `D:\Cache\mpa-bridge\` for grading). Component 1 delegates structural shape to mpa-atlas/schema/*.json (Draft 2020-12) and runs §3-extras (capacity, tower convergence) on top.

## v0.2 readiness gates

> v0.2 ready when habit-extinction reference driver lands and components 3–6 work cross-substrate.

Not started. Triggered by habit-extinction reference driver landing in mpa-atlas (see [`mpa-atlas/docs/handoff_next_session.md`](https://github.com/ronviers/mpa-atlas/blob/main/docs/handoff_next_session.md) Open item 2).

## Discipline notes

- **Substrate-neutral by construction.** No substrate-specific logic anywhere in `src/mpa_bridge/`. Drivers carry that. Component 6 reads v9 + reference-drivers as system context for Claude; the tool itself encodes none of it.
- **Mechanical-only validation.** Components 1, 2, 4 are strictly deterministic. Same artifact → same diagnostics. The assist surface is forbidden inside validators — that's the load-bearing carve-out for CI to mean anything.
- **DBS-backward via Claude.** Components 3, 5, 6 (compile, discover, gap-report) are the synthesis surfaces. They call `assist.ask` because the framework's commitment to *demand-bounded sufficiency* says the tool produces *some* answer rather than blocking on missing inputs. The cache at `D:\Cache\mpa-bridge\` doubles as a gradable run-log.
- **Diagnostics carry stable codes.** Format: `RFC<n>.INV.<k>` for per-RFC §3 invariants, `RFC3.C<n>` / `RFC3.K<n>` for cross-artifact predicates, `RFCV.S<n>.<tag>` for RFC-V vocabulary checks, `BRIDGE.<TAG>` for tool-internal status. Tests assert on codes; diagnostics are exchange surface with CI.

## Known gaps

- **Spec inv. 4 (scale-monotonicity) not yet implemented.** Schema admits multi_band shape; the cross-band monotonicity check (no inverse regime transitions, γ doesn't strengthen at wider τ_obs) lives in code and is deferred until a multi-band spec lands as a stress case.
- **Spec inv. 2 (sign-canonicity) is trust-based.** No mechanical signal distinguishes a canonical-sign from substrate-native-sign spec; the discipline lives at the driver layer.
- **Sig inv. 6 sampling adequacy** (sample density vs declared precision) is substrate-dependent; deferred to driver tolerance.
- **RFC-V checks are narrow by design.** High-precision-low-recall — three warning rules and a coverage report. Broader checks need a LaTeX-aware parser, not in v0.1 scope.
