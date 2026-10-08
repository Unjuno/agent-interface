"""Host-only prototype of an atomic one-shot claim for the #5156 launcher."""
from __future__ import annotations

import json
import os
import sys
from datetime import timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ALLOCATION_DIR = ROOT / "research" / "live_control" / "owner_keyup_formal_x11_5156_20261001_06"
if str(ALLOCATION_DIR) not in sys.path:
    sys.path.insert(0, str(ALLOCATION_DIR))
import invoke_allocation


def run_reserved(snapshot, now, run_candidate, run_auditor, results_dir):
    """Atomically reserve this output slot before entering the existing gate.

    The claim is intentionally permanent: a crash after reservation fails
    closed and requires a fresh allocation instead of permitting a retry.
    """
    results_dir = Path(results_dir)
    claim_path = results_dir / "INVOCATION_CLAIM.json"
    payload = {
        "allocation": invoke_allocation.ALLOCATION,
        "claimed_at_utc": now.astimezone(timezone.utc).isoformat(),
        "state": "RESERVED_NO_RETRY",
    }
    try:
        descriptor = os.open(
            str(claim_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
    except FileExistsError:
        return 2
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return invoke_allocation.run_one_shot(
        snapshot, now, run_candidate, run_auditor, results_dir
    )
