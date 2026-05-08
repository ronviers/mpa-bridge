"""Delegate structural validation to mpa-atlas JSON Schemas.

The schemas are the canonical machine-readable form of each RFC's §2 + §3
schema-expressible invariants. We run them first; the cross-field §3
invariants that exceed schema (capacity bound, tower convergence,
scale-monotonicity, sampling adequacy) live in validate_single.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .diagnostics import Diagnostic, Severity

ATLAS_SCHEMA = Path(r"H:\mpa-atlas\schema")

KIND_TO_SCHEMA = {
    "spec": "spec-object.v0.2.json",
    "signature": "fdr-signature.v0.1.json",
    "driver_profile": "driver-profile.v0.2.json",
    "r_doc": "realizer-interface.v0.1.json",
}

_VALIDATOR_CACHE: dict[str, Draft202012Validator] = {}


def _build_validators() -> dict[str, Draft202012Validator]:
    if not ATLAS_SCHEMA.exists():
        return {}
    schemas = {f.name: json.loads(f.read_text(encoding="utf-8")) for f in ATLAS_SCHEMA.glob("*.json")}
    registry = Registry().with_resources(
        (name, Resource.from_contents(s)) for name, s in schemas.items()
    )
    return {
        kind: Draft202012Validator(schemas[fname], registry=registry)
        for kind, fname in KIND_TO_SCHEMA.items()
        if fname in schemas
    }


def _get_validator(kind: str) -> Draft202012Validator | None:
    if not _VALIDATOR_CACHE:
        _VALIDATOR_CACHE.update(_build_validators())
    return _VALIDATOR_CACHE.get(kind)


def schema_validate(doc: Any, kind: str, source: str = "") -> Iterable[Diagnostic]:
    validator = _get_validator(kind)
    if validator is None:
        yield Diagnostic(
            "BRIDGE.SCHEMA_MISSING", Severity.WARNING,
            f"schema for {kind!r} not found at {ATLAS_SCHEMA}; "
            "structural validation skipped (cross-field §3 checks still run)",
            source,
        )
        return
    code = f"SCHEMA.{kind}"
    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        path = ".".join(str(p) for p in err.absolute_path) if err.absolute_path else ""
        yield Diagnostic(code, Severity.ERROR, err.message, source, path)
