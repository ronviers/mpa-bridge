# mpa-bridge — next-session handoff

**Status of tool side:** v0 in progress. Seven components scaffolded; 1, 3, 4, 5, 6, 7 working at various depths and 2 scaffolded — see [docs/status.md](status.md) for current readiness against the v0.1 / v0.2 gates. Cache + run-log at `D:\Cache\mpa-bridge\`. Repo is public at <https://github.com/ronviers/mpa-bridge>.

**This file** captures the open items for follow-up sessions. Listed in dependency order: operations manual makes runs reproducible; runs stress-test the manual.

Read in this order before picking up any item:

1. This file.
2. [README](../README.md) — what mpa-bridge is, seven-component table, v0.1 / v0.2 readiness gates.
3. [CLAUDE.md](../CLAUDE.md) — implementation discipline (substrate-neutral, mechanical-only validators, DBS-backward via Claude).
4. [docs/status.md](status.md) — current readiness against gates.
5. [mpa-atlas RFCs](https://github.com/ronviers/mpa-atlas/tree/main/rfcs) — the contracts being validated.

---

## Open item 1 — Operations manual (`docs/operations.md`)

Produce `docs/operations.md` — user-facing how-to-use guide for mpa-bridge. README says what mpa-bridge **is**; status.md says what's **working**; operations.md says **how to use it**. Read by: someone with a real spec / driver / unknown data who needs to know which subcommand to run and how to interpret output.

### Six sections in order

1. **Quickstart.** Install (`pip install -e .`), config (`ANTHROPIC_API_KEY` presence, schemas at `H:/mpa-atlas/schema/`, cache at `D:/Cache/mpa-bridge/`), one canonical first-run command and what to expect on stdout / stderr.
2. **Subcommand reference.** Per `validate`, `constellation`, `compile`, `round-trip`, `discover`, `gap-report`, `vocab`: signature, required inputs, where outputs go, exit-code convention (0 = clean, 1 = errors found, 2 = bad usage), one minimal worked example.
3. **Workflows.** Three composed scenarios:
   - "I have a new substrate." `discover` → either `compile` (driver fits) or `gap-report` (driver missing).
   - "I have a spec and want to certify a substrate." `validate spec` → `compile` → `constellation` → `round-trip`.
   - "I'm authoring an RFC or driver." `vocab` against the canonical-label registry; iterate.
4. **Diagnostic codes.** Table mapping every code (`SCHEMA.<kind>`, `RFC1.INV.<n>`, `RFC3.C<n>`, `RFC3.K<n>`, `RFC-S5.*`, `RFCV.S<n>.<tag>`, `BRIDGE.<TAG>`) to meaning, severity, and (where relevant) the RFC section it references. Tests assert on these codes; CI consumes them; users grep them.
5. **Cache management + grading.** What lives in `D:/Cache/mpa-bridge/`, how to inspect a record (`jq`, `python -m json.tool`), how to clear stale entries, how to use cache files as run logs for after-the-fact grading. The cache *is* the run log.
6. **Determinism + when to trust what.** Mechanical surfaces (1, 2, 4, 7 — same input, same output) vs. Claude-assisted (3, 5, 6 — local-cached but stochastic on cache miss). CI consumes only mechanical-surface verdicts; synthesis surfaces are advisory and gradable.

### Out of scope

- **Library-API reference** (programmatic use of `mpa_bridge` as a Python module). Separate doc when wanted.
- **Architecture / internals.** Lives in `CLAUDE.md` and per-module docstrings.
- **Contribution guide.** Defer until external contributors exist.

### Failure modes

- **Re-narrating the README.** README says what; operations manual says how. If a section reads like a feature list, rewrite as a workflow.
- **Code listings without expected output.** Every worked example shows the command AND the expected stdout/stderr on the canonical fixture.
- **Diagnostic-code table that drifts.** The table must match what `src/mpa_bridge/` actually emits. Cheapest enforcement: a smoke script that runs the full suite, collects emitted codes, and diffs against the table.

**Done when:** `docs/operations.md` exists with all six sections; README links to it under a "How to use" section that supersedes the current minimal usage block.

**Effort:** ~half a day for a tight first pass.

---

## Open item 2 — Runs and working libraries

Move mpa-bridge from "passes its smoke tests" to "has been used on real cases, has a library of worked examples, has accumulated friction notes." Two deliverables:

1. **Examples library** at `examples/<case-name>/` — real-flavored specs, R_docs, signatures, gap reports, organized by case.
2. **Case studies** at `docs/cases/<case-name>.md` — narrative writeups: what was attempted, what worked, what surfaced.

Runs are how we find out which scaffolding is correctly thin vs. brittle. Working libraries make future sessions cheaper — they start with concrete examples instead of synthesizing from scratch.

### Round 1 cases (independent; can be tackled in parallel)

1. **Surface-code QEC end-to-end.** Build a real spec from v9 §FDR (the surface-code identification paragraph) and the surface-code reference driver. Compile under each I1..I5. Validate constellation. Run round-trip against synthetic identity measurements. Write up: did each intent compile cleanly? Were the I2/I3/I4 `RFC-S5.METRIC_NA` infos surfaced as expected? Where did Sonnet need prompt help?
2. **Cross-substrate gap report.** 3–5 substrate descriptions from existing `mpc-*` repos (mpc-glass aging, mpc-brain habit-extinction, mpc-quantum syndrome streams, mpc-sat XOR). Run `gap-report` on each; compare to what's pinned in the corresponding repo's driver-in-progress. Where did the LLM see what we already know? Where did it miss?
3. **Discover ranking calibration.** Run `discover` on the same 3–5 + a synthetic mismatch. Verify ranking matches intuition (each substrate's data scores high on its own driver, low on others; synthetic mismatch scores low across the board).
4. **Vocabulary check pass.** Run `vocab` on every RFC, the architectural block-in, `v9_compressed.md`, the handoffs. Catalog false-positive rate vs. real catches; tighten regex rules in `vocabulary.py` based on actual experience.

### Per-case directory structure

```
examples/<case-name>/
├── README.md           # one paragraph: what is this case
├── spec.json           # the spec object (when applicable)
├── driver.json         # the driver profile (or pointer to mpa-atlas/reference-drivers/)
├── intent_<I1..I5>/
│   ├── compiled.json   # output of compile under this intent
│   ├── round_trip.txt  # output of round-trip vs identity measured
│   └── notes.md        # what was learned for this intent
└── gap_report.md       # if run, the gap-report output verbatim
```

Each case study lives at `docs/cases/<case-name>.md` and points back to its `examples/<case-name>/` directory.

### Friction log + fixture promotion

- `docs/friction.md` — running list of awkward surfaces, prompt failures, missing affordances. Each entry: trigger condition, what happened, suggested fix (or "deferred — needed v0.2").
- When a real-case artifact stabilizes (compiles cleanly, validates, round-trips), promote a sanitized copy to `tests/fixtures/` so the test suite gets richer beyond minimal-valid.

### Failure modes

- **Producing artifacts the tool can't ingest.** Every example file is regression-testable: `python -m mpa_bridge validate <file>` returns rc=0. If a hand-written example fails the validator, the example is wrong OR it's revealing a real validator gap → file in `friction.md`.
- **Case studies that just narrate the tool output.** A case study adds insight: where the LLM missed, where the prompt had to be guided, where the discipline held vs. wobbled.
- **Letting the cache bloat without grading.** Each case produces a brief grade in its case study.
- **Promoting artifacts to fixtures without sanitizing.** Double-check no proprietary or ungeneralized content leaks into `tests/fixtures/`.

**Done when:** `examples/` has Round 1 cases; `docs/cases/` has writeups; `docs/friction.md` exists.

**Effort:** 1–2 days for Round 1; subsequent cases ~half-day each.

---

## Inherited soft blockers

Preserved from prior session unblock work; absorbed here on its deletion. None block runs; each is a small fragility worth addressing when convenient.

- **No CI on either repo.** Add `pytest -q` to mpa-bridge and schema-validation to mpa-atlas once runs produce artifacts that benefit from CI protection.
- **Compile prompt's I1..I5 mapping is unverified.** Round-trip against hand-built reference per intent surfaces this; closing happens via runs, not by adding more prose.
- **Compile may cite RFC sections that don't exist.** Tighten `compile_.py` SYSTEM_PROMPT with "do not invent section numbers; quote verbatim or omit"; or post-validate by extracting cited RFC references and grep-checking. Defer the post-validator until runs surface a real harm case.
