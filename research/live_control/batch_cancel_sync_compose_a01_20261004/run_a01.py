"""Frozen once-only candidate entry point; writes raw before audit."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests"))
from test_batch_cancel_sync_composition import run_scenarios

raw = {
    "schema": "batch-cancel-sync-composition-a01-run-v1",
    "started_at": datetime.now(timezone.utc).isoformat(),
    "candidate_sha256": __import__("hashlib").sha256(
        (ROOT / "candidate/input_owner_v12_composed.py").read_bytes()
    ).hexdigest(),
}
try:
    raw.update(run_scenarios())
    raw["candidate_exit"] = 0
except BaseException as exc:
    raw.update({"candidate_exit": 1, "candidate_error": repr(exc)})
    raise
finally:
    raw["ended_at"] = datetime.now(timezone.utc).isoformat()
    (ROOT / "raw/trace.json").write_text(
        json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

print(json.dumps({"candidate_exit": raw["candidate_exit"], "cases": len(raw.get("cases", []))}))
