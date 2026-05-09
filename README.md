# mpa-bridge

Protocol tool for [mpa-atlas](https://github.com/ronviers/mpa-atlas). Operates on the artifacts the RFCs govern: spec objects, FDR signatures, driver profiles, realizer-interface documents.

The protocol's checkable surface. Without the tool, the protocol is prose.

## What it does (status: v0 in progress)

Seven components, per [`mpa-atlas/architecture/handoff_protocol-tool.md`](https://github.com/ronviers/mpa-atlas/blob/main/architecture/handoff_protocol-tool.md):

| # | Component | Status |
|---|---|---|
| 1 | Single-artifact validator (schema-delegated + §3 extras) | working |
| 2 | Constellation validator (RFC-3 C1–C5, K1) | scaffolded |
| 3 | Compiler (spec × intent → R_doc, RFC-RI) | working (Sonnet-assisted, validator-gatekept) |
| 4 | Round-trip checker (RFC-S §5) | working (I1 + I5 metrics; I2/I3/I4 emit METRIC_NA) |
| 5 | Driver discoverer (DBS-backward) | working (Claude-assisted, Haiku) |
| 6 | Characterization-gap reporter (DBS-backward) | working (Claude-assisted, Haiku) |
| 7 | Vocabulary checker (RFC-V) | working (narrow) |

## Assist surface (DBS-backward operational vehicle)

Synthesis surfaces (currently component 6, soon 3 and 5) call Claude through a thin wrapper at [`src/mpa_bridge/assist.py`](src/mpa_bridge/assist.py). Cache + run-log at `D:\Cache\mpa-bridge\` — every call writes a JSON record with model, system, prompt, response, timestamp, and token usage. The cache file *is* the log; grade runs after the fact by reading them.

Validators (components 1, 2, 4) stay strictly mechanical. The contract: same artifact → same diagnostics, every run.

Model assignment: Haiku 4.5 by default for synthesis surfaces; Sonnet 4.6 reserved for harder structured output (compile, when wired); Opus 4.7 only when a problem genuinely warrants it.

v0.1 ships when 1, 2, 7 work end-to-end against existing mpa-atlas artifacts and 3, 4 work against the surface-code reference driver. v0.2 lands when habit-extinction reference driver lands and 3–6 work cross-substrate.

## Install

Python ≥ 3.11. From a checkout:

```
pip install -e .
```

## Usage

```
mpa-bridge validate <artifact.json|.yaml>
mpa-bridge constellation --spec S.json --driver D.json --rdoc R.json [--signatures sig1.json sig2.json ...]
mpa-bridge compile --spec S.json --intent I1 --driver D.json [--output R.json]
mpa-bridge round-trip --rdoc R.json --measured sig1.json [sig2.json ...]
mpa-bridge discover <data.md>
mpa-bridge gap-report <data.md>
mpa-bridge vocab <document.md>
```

All seven components ship. `round-trip` v0.1 implements I1 + I5 metrics; I2/I3/I4 emit `RFC-S5.METRIC_NA` info diagnostics until a substrate-realizer pair lands.

Diagnostics carry stable codes:

- `SCHEMA.<kind>` — structural validation (delegated to mpa-atlas/schema/*.json)
- `RFC1.INV.<n>` — §3 invariants exceeding schema (capacity, tower-convergence)
- `RFC3.C<n>` / `RFC3.K<n>` — cross-artifact consistency / completeness
- `RFCV.S<n>.<tag>` — RFC-V vocabulary checks
- `BRIDGE.<TAG>` — tool-internal status

Component 1 delegates structural shape to the JSON Schemas in mpa-atlas; if the schemas aren't on disk, structural validation falls back to a `BRIDGE.SCHEMA_MISSING` warning and the §3-extras still run.

## Discipline

This repo is downstream of mpa-atlas. The thin-RFC discipline that governs mpa-atlas does **not** govern this code — implementation code is normal engineering. See [CLAUDE.md](CLAUDE.md).

The tool is **substrate-neutral by construction**. It reads driver profiles; it does not encode v9 mathematical content or any substrate-specific reading rule. If you find yourself implementing operator algebra inside the tool, stop — that's a driver's job (or v9's).

## Repo layout

```
src/mpa_bridge/
  cli.py                     entry point
  diagnostics.py             Diagnostic dataclass + RFC-coded rule registry
  artifacts.py               load + identify spec/signature/driver/r_doc
  vocabulary.py              component 7
  validate_single.py         component 1
  validate_constellation.py  component 2
  compile_.py round_trip.py discover.py gap_report.py   stubs (3, 4, 5, 6)
tests/                       pytest fixtures + smoke
docs/status.md               readiness gates against the handoff
```

## License

Public, unlicensed (copyright retained). Bring up if you need terms.
