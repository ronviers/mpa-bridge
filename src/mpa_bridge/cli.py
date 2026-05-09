"""Command-line entry point.

Subcommands map to the seven components named in README.md.
Components 3-6 are stubs in v0.1; they print their planned interface and
exit non-zero with code BRIDGE.STUB.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from . import artifacts, validate_constellation, validate_single, vocabulary
from .diagnostics import Diagnostic, Severity, print_all
from . import compile_, round_trip, discover, gap_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mpa-bridge", description="Protocol tool for mpa-atlas.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_validate = sub.add_parser("validate", help="Component 1: validate a single artifact (auto-detect kind).")
    p_validate.add_argument("path", help="Path to spec / signature / driver-profile / R_doc (.json or .yaml).")

    p_const = sub.add_parser("constellation", help="Component 2: validate a constellation against RFC-3.")
    p_const.add_argument("--spec", required=True, help="Path to spec object.")
    p_const.add_argument("--driver", required=True, help="Path to driver profile.")
    p_const.add_argument("--rdoc", required=True, help="Path to R_doc.")
    p_const.add_argument("--signatures", nargs="*", default=[], help="Optional signature files.")

    p_vocab = sub.add_parser("vocab", help="Component 7: RFC-V vocabulary check on a markdown/text document.")
    p_vocab.add_argument("path", help="Path to a document.")

    p_compile = sub.add_parser("compile", help="Component 3: spec × intent → R_doc (Claude-assisted).")
    p_compile.add_argument("--spec", required=True)
    p_compile.add_argument("--intent", required=True, choices=["I1", "I2", "I3", "I4", "I5"])
    p_compile.add_argument("--driver", required=True)
    p_compile.add_argument("--output", default=None, help="Write R_doc here; otherwise print to stdout.")

    p_rt = sub.add_parser("round-trip", help="Component 4: forward + round-trip error per RFC-S §5.")
    p_rt.add_argument("--rdoc", required=True)
    p_rt.add_argument("--measured", nargs="+", required=True, help="One or more measured FDR signature files.")

    p_disc = sub.add_parser("discover", help="Component 5: rank drivers against data (Claude-assisted).")
    p_disc.add_argument("path", help="Path to data description (text/markdown).")

    p_gap = sub.add_parser("gap-report", help="Component 6: characterization-gap reporter (DBS-backward).")
    p_gap.add_argument("path", help="Path to data description (text/markdown).")

    args = parser.parse_args(argv)

    if args.cmd == "validate":
        return _run_validate(args.path)
    if args.cmd == "constellation":
        return _run_constellation(args.spec, args.driver, args.rdoc, args.signatures)
    if args.cmd == "vocab":
        return _run_vocab(args.path)
    if args.cmd == "compile":
        return compile_.run(args.spec, args.intent, args.driver, args.output)
    if args.cmd == "round-trip":
        return round_trip.run(args.rdoc, args.measured)
    if args.cmd == "discover":
        return discover.run(args.path)
    if args.cmd == "gap-report":
        return gap_report.run(args.path)
    return 2


def _run_validate(path: str) -> int:
    p = Path(path)
    if not p.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    try:
        doc = artifacts.load(p)
    except Exception as e:
        print(f"error: failed to parse {path}: {e}", file=sys.stderr)
        return 2
    kind = artifacts.identify(doc)
    diags = validate_single.validate(doc, kind, source=str(p))
    diags.insert(0, Diagnostic(
        "BRIDGE.IDENTIFY", Severity.INFO,
        f"identified artifact as {kind!r}",
        str(p),
    ))
    return print_all(diags)


def _run_constellation(spec_path: str, driver_path: str, rdoc_path: str, sig_paths: list[str]) -> int:
    try:
        spec = artifacts.load(spec_path)
        driver = artifacts.load(driver_path)
        rdoc = artifacts.load(rdoc_path)
        signatures = [artifacts.load(s) for s in sig_paths]
    except Exception as e:
        print(f"error: failed to load constellation: {e}", file=sys.stderr)
        return 2
    sources = {
        "spec": spec_path,
        "driver": driver_path,
        "r_doc": rdoc_path,
        **{f"signature[{i}]": s for i, s in enumerate(sig_paths)},
    }
    diags = validate_constellation.validate(spec, driver, rdoc, signatures, sources)
    return print_all(diags)


def _run_vocab(path: str) -> int:
    p = Path(path)
    if not p.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    diags = vocabulary.check_file(p)
    return print_all(diags)
