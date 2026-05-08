# Discipline: implementation, not protocol

This repo is the **protocol tool** for [mpa-atlas](https://github.com/ronviers/mpa-atlas). It is downstream of the protocol — it reads, validates, compiles, and round-trips against artifacts the mpa-atlas RFCs govern.

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

## Failure modes the handoff names

Worth re-listing for prompt-recall:

- Encoding v9 in the tool → keep §6 surgical; everything else reads driver profiles only.
- Building substrate-specific logic → push it into a driver.
- Failing on unknown data instead of declaring the gap → DBS-backward is component 6's whole point.
- Pretending to validate cross-artifact consistency from a single artifact → that's component 1's job; component 2 needs the constellation.
- Bloating beyond the seven components → if a new top-level surface emerges, ask which RFC it serves. If none, it's substrate-specific (driver) or authoring (mpa-character), not here.

## Coordinates

| Document | Where |
|---|---|
| Tool's plan-of-record | [mpa-atlas/architecture/handoff_protocol-tool.md](https://github.com/ronviers/mpa-atlas/blob/main/architecture/handoff_protocol-tool.md) |
| Schema files (forthcoming, dependency for component 1) | [mpa-atlas/architecture/handoff_schema_files.md](https://github.com/ronviers/mpa-atlas/blob/main/architecture/handoff_schema_files.md) |
| Reference driver (target for components 3, 4, 5, 6) | [mpa-atlas/reference-drivers/surface-code-qec.md](https://github.com/ronviers/mpa-atlas/blob/main/reference-drivers/surface-code-qec.md) |
| RFCs (the contracts being validated) | [mpa-atlas/rfcs/](https://github.com/ronviers/mpa-atlas/tree/main/rfcs) |
| v9 (rigor source — not consumed by tool except §6) | [mpa-atlas/framework/v9_compressed.md](https://github.com/ronviers/mpa-atlas/blob/main/framework/v9_compressed.md) |
