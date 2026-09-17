"""Preformal harness repair for Issue #869.

The exact v2 Backend.raw() emits ordinary input_admission for key-down as well as
input_release_rpc for key-up. The v1 harness incorrectly required the entire
emitted list to contain exactly one row. This wrapper preserves the exact v2 raw
path and forwards only the release telemetry row to the existing v1 result
collector. No scientific threshold, schedule, source pin, X11 behavior, or formal
allocation is changed.
"""
from __future__ import annotations

import run_case as base

_original_loader = base.load_candidate_backend


def _release_only_loader(owner, lease, case_id: str, emitted: list[dict]):
    # Use the original exact-v2 loader, but keep its complete emission surface
    # separate from the release-edge measurement result. Admission emission is
    # expected and is not a release receipt.
    all_rows: list[dict] = []
    backend = _original_loader(owner, lease, case_id, all_rows)

    def emit(row: dict) -> None:
        all_rows.append(row)
        if row.get("event") == "input_release_rpc":
            emitted.append(row)

    backend.emit = emit
    return backend


base.load_candidate_backend = _release_only_loader


if __name__ == "__main__":
    base.main()
