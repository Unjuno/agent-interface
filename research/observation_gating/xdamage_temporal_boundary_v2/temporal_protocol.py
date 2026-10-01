"""Pure protocol helpers for the XDamage temporal-boundary successor.

No X server calls live here. This module is intentionally easy to audit.
"""
from dataclasses import dataclass
from enum import Enum


class Case(str, Enum):
    QUIET = "QUIET"
    REPAINT_A = "REPAINT_A"
    PERSIST_B = "PERSIST_B"
    ABA_1PX = "ABA_1PX"
    ABA_2X2 = "ABA_2X2"
    ABA_8X8 = "ABA_8X8"


@dataclass(frozen=True)
class Observation:
    case: Case
    baseline_rgb: bytes
    middle_rgb: bytes
    endpoint_rgb: bytes
    damage_count: int
    width: int = 64
    height: int = 64

    def validate(self) -> None:
        n = self.width * self.height * 3
        if self.width != 64 or self.height != 64:
            raise ValueError("unexpected drawable geometry")
        if any(len(frame) != n for frame in
               (self.baseline_rgb, self.middle_rgb, self.endpoint_rgb)):
            raise ValueError("RGB byte length mismatch")
        if type(self.damage_count) is not int or self.damage_count < 0:
            raise ValueError("invalid damage count")


def schedule() -> list[tuple[int, Case]]:
    """Session-rotated six-case order, deterministic and one-based."""
    cases = list(Case)
    rows = []
    for session in range(8):
        rotation = session % len(cases)
        for offset in range(len(cases)):
            rows.append((session + 1, cases[(rotation + offset) % len(cases)]))
    return rows


def classify(row: Observation, *, identity_valid: bool = True,
             coverage_complete: bool = True, source_fresh: bool = True) -> str:
    """Classify only scoped XDamage evidence; never grant action authority."""
    row.validate()
    if not identity_valid or not coverage_complete or not source_fresh:
        return "UNKNOWN"
    if row.damage_count:
        return "DAMAGE_OBSERVED"
    if row.case is Case.QUIET and row.baseline_rgb == row.endpoint_rgb:
        return "NO_DAMAGE_OBSERVED_SCOPED"
    return "UNKNOWN"


def gate(row: Observation) -> dict[str, object]:
    """Model O1 visibility using endpoint bytes only."""
    row.validate()
    changed = row.baseline_rgb != row.endpoint_rgb
    return {
        "endpoint_changed": changed,
        "o1_forwards_endpoint": changed,
        "middle_used_by_candidate": False,
        "action_authority": False,
        "damage_disposition": classify(row),
    }


def expected(case: Case) -> tuple[bool, bool, bool]:
    """(middle differs from baseline, endpoint differs, damage expected)."""
    if case is Case.QUIET:
        return False, False, False
    if case is Case.REPAINT_A:
        return False, False, True
    if case is Case.PERSIST_B:
        return True, True, True
    return True, False, True


def decision(rows: list[Observation]) -> str:
    """Closed-world 48-row acceptance. Invalid coverage is HOLD, never PASS."""
    if len(rows) != 48:
        return "HOLD_COVERAGE"
    observed = {}
    for row in rows:
        row.validate()
        key = (row.case, row.baseline_rgb, row.middle_rgb, row.endpoint_rgb)
        observed[key] = observed.get(key, 0) + 1
    counts = {case: 0 for case in Case}
    for row in rows:
        counts[row.case] += 1
    if any(counts[c] != 8 for c in Case):
        return "HOLD_COVERAGE"
    for row in rows:
        middle, endpoint, damage = expected(row.case)
        actual = (row.baseline_rgb != row.middle_rgb,
                  row.baseline_rgb != row.endpoint_rgb,
                  row.damage_count > 0)
        if actual != (middle, endpoint, damage):
            return "FAIL_FROZEN_MATRIX"
    return "PASS_XDAMAGE_TEMPORAL_BOUNDARY_V2_SCOPED"
