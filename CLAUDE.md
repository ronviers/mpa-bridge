# Discipline: implementation, not protocol

This repo is the **protocol tool** for [mpa-atlas](https://github.com/ronviers/mpa-atlas). It is downstream of the protocol — it reads, validates, compiles, and round-trips against artifacts the mpa-atlas RFCs govern.

## Program-level discipline

This repo is a **validator** per [`H:/mpa-central/METHODOLOGY.md`](../mpa-central/METHODOLOGY.md) Cut 4 — round-trip discipline on artifacts the mpa-atlas RFCs govern. Protocol-shaped surfaces inherit thin-RFC discipline (next section); implementation code is normal engineering.

## What thin-RFC discipline does and does not govern here

mpa-atlas carries [thin-RFC discipline](https://github.com/ronviers/mpa-atlas/blob/main/CLAUDE.md). That discipline governs **protocol-shaped artifacts** (RFC documents, schema files, exchange contracts). It does **not** govern this repo's implementation code — same carve-out as `mpa-character` makes for its UI/engine/tests.

Concretely:

- **Source code** (`src/mpa_bridge/**`) — normal engineering. Write what's clearest; refactor when shape demands; do not target a page budget.
- **Diagnostic output** (`diagnostics.py` messages, gap-report prose) — keep tight. Diagnostics are exchange surface with the user and CI; one line per finding, RFC-coded. Brevity earns its keep here.
- **Docs and READMEs** — operational meta, written for clarity over brevity. Still: short is better.
- **Tests** — normal engineering. Fixtures may be verbose to capture artifact shapes faithfully.

## Substrate-neutral by construction

The tool **must not** encode v9's mathematical content or any substrate-specific reading rule. Drivers carry substrate-specific logic; the tool reads driver profiles, not v9 directly (one exception: §6 characterization-gap reporter reads v9's substrate-conditional reading rules to find the closest substrate class for a gap report).

If a check requires substrate-specific knowledge to compute, it belongs in the driver, not here. Test the discipline against any new validator: would this check produce the same answer for surface-code QEC and habit-extinction substrates given equivalent inputs? If no, it's substrate-specific and out of scope.

## Architecture notes

- **Modular.** Each of the seven components is independently invocable. Tool UX is one CLI subcommand per component, or a workflow that composes them.
- **Schema-driven.** JSON Schemas at `mpa-atlas/schema/*.json` are the validator's source-of-truth. RFC content is operational reference; schemas are the machine-readable form.
- **Mechanical-only validation.** Components 1, 2, 4, 7 are strictly deterministic — same artifact, same diagnostics. The assist surface is forbidden inside validators; that's the load-bearing carve-out for CI to mean anything.
- **DBS-backward via Claude.** Components 3, 5, 6 are synthesis surfaces. They call `assist.ask` because demand-bounded sufficiency says the tool produces *some* answer rather than blocking on missing inputs. Cache at `D:\Cache\mpa-bridge\` doubles as a gradable run-log.

## Out of scope

- **Substrate-specific realization.** Realizer search algorithms (find substrate parameters that produce the canonical structure) live in `mpc-*` driver/realizer pairs, not here.
- **Building drivers.** That's substrate-research work in `mpc-*` repos.
- **Encoding v9's mathematical content.** Tool reads driver profiles; v9 is the rigor source. One exception: component 6 reads v9 substrate-conditional reading rules to find the closest substrate class for a gap report.
- **Authoring environments.** mpa-character is the authoring environment; the tool is the validator/compiler/checker, not the editor.
- **Bloating beyond the seven components.** If a new top-level surface emerges, ask which RFC it serves. If none, it's substrate-specific (driver) or authoring (mpa-character), not here.

## Failure modes

- Encoding v9 in the tool → keep §6 surgical; everything else reads driver profiles only.
- Building substrate-specific logic → push into a driver.
- Failing on unknown data instead of declaring the gap → DBS-backward is component 6's whole point.
- Pretending to validate cross-artifact consistency from a single artifact → that's component 1's job; component 2 needs the constellation.

## Coordinates

| Document | Where |
|---|---|
| Open work for this repo | [docs/handoff_next_session.md](docs/handoff_next_session.md) |
| Component readiness | [docs/status.md](docs/status.md) |
| RFCs (the contracts being validated) | [mpa-atlas/rfcs/](https://github.com/ronviers/mpa-atlas/tree/main/rfcs) |
| Schema files (component 1's source-of-truth) | [mpa-atlas/schema/](https://github.com/ronviers/mpa-atlas/tree/main/schema) |
| Reference driver (target for components 3, 4, 5, 6) | [mpa-atlas/reference-drivers/surface-code-qec.md](https://github.com/ronviers/mpa-atlas/blob/main/reference-drivers/surface-code-qec.md) |
| Architectural commitments (cross-RFC) | [mpa-atlas/architecture/MPA_Architectural_Block-In.md](https://github.com/ronviers/mpa-atlas/blob/main/architecture/MPA_Architectural_Block-In.md) |
| v9 (rigor source — not consumed by tool except §6) | [mpa-atlas/framework/v9_compressed.md](https://github.com/ronviers/mpa-atlas/blob/main/framework/v9_compressed.md) |
