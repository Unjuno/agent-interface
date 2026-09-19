"""Formal MAP01 bounded-recovery mechanism v4 runner.

V4 preserves the frozen three-pair mechanism condition while replacing the older
normal-release-only accounting adapter with the fail-closed windowed any-key
occupancy implementation retained after the local interruption matrix.
"""
from __future__ import annotations

ALLOCATION_ID = "map01-recovery-cover-mechanism-live-v4-01"
WORKFLOW_PATH = ".github/workflows/map01-recovery-cover-mechanism-live-v4-01.yml"


def configure():
    import map01_recovery_cover_matched_v2_runner as base
    from map01_recovery_cover_mechanism_v4_measurement import fallback_input_bounds

    base.ALLOCATION_ID = ALLOCATION_ID
    base.EXPECTED_WORKFLOW_PATH = WORKFLOW_PATH
    base.fallback_input_bounds = fallback_input_bounds
    return base


def main() -> None:
    configure().main()


if __name__ == "__main__":
    main()
