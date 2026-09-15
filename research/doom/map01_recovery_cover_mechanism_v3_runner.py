from __future__ import annotations
import map01_recovery_cover_matched_v2_runner as base

ALLOCATION_ID = "map01-recovery-cover-mechanism-live-v3-01"
WORKFLOW_PATH = ".github/workflows/map01-recovery-cover-mechanism-live-v3-01.yml"


def configure() -> None:
    base.ALLOCATION_ID = ALLOCATION_ID
    base.EXPECTED_WORKFLOW_PATH = WORKFLOW_PATH


def main() -> None:
    configure()
    base.main()


if __name__ == "__main__":
    main()
