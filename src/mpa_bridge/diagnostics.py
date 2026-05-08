"""Diagnostic carrier and severity.

Every check emits Diagnostic records. The `code` field names the RFC-rule
the diagnostic flags (e.g., RFC1.INV.5, RFC3.C1, RFC3.K1, RFCV.S4.epsilon).
Stable codes let callers grep, filter, and report mechanically.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: Severity
    message: str
    artifact: str = ""
    path: str = ""

    def format(self) -> str:
        loc = f"{self.artifact}:{self.path}" if self.artifact or self.path else ""
        loc_part = f" [{loc}]" if loc else ""
        return f"{self.severity.value}: {self.code}: {self.message}{loc_part}"


def has_errors(diags: Iterable[Diagnostic]) -> bool:
    return any(d.severity is Severity.ERROR for d in diags)


def print_all(diags: Iterable[Diagnostic]) -> int:
    """Print diagnostics in stable order; return non-zero if any error."""
    diags = list(diags)
    for d in diags:
        print(d.format())
    return 1 if has_errors(diags) else 0
