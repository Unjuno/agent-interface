"""Capture the real v3 wrapper plus retained batch-adapter receipt."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOOM = HERE.parents[1]
sys.path.insert(0, str(DOOM))

from test_doom_retained_input_backend_v3 import actual_wrapper_batch_receipt

candidate = {
    "schema": "input-release-wrapper-batch-candidate-v1",
    "fixture": "actual input_transition_owner_v3 wrapper + retained adapter; injected in-memory owner",
    "record": actual_wrapper_batch_receipt(),
}
(HERE / "candidate.json").write_text(
    json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(candidate, sort_keys=True))
