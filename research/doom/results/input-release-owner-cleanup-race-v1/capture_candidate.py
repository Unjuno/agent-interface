"""Capture a cleanup-overlaps-explicit-up receipt from current sources."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOOM = HERE.parents[1]
sys.path.insert(0, str(DOOM))

from test_doom_retained_input_backend_v3 import actual_wrapper_batch_evidence

evidence = actual_wrapper_batch_evidence(cleanup_during_up=True)
candidate = {
    "schema": "input-release-owner-cleanup-race-candidate-v1",
    "fixture": "injected owner-release record is timestamped inside wrapper call; explicit up is simulated as a no-op",
    "record": evidence["receipt"],
    "owner_records": evidence["owner_records"],
}
(HERE / "candidate.json").write_text(
    json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(candidate, sort_keys=True))
