"""Run the missing-owner-id release-batch construction control."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOOM = HERE.parents[1]
sys.path.insert(0, str(DOOM))

import test_doom_retained_input_backend_v3 as harness

backend = harness.make_backend({"a"}, harness.Owner(owner_id=None))
backend.raw("a", False)
record = backend.emitted[0]
candidate = {
    "schema": "input-release-owner-identity-candidate-v1",
    "fixture": "synthetic owner returns owner_id=null for release and state sample",
    "record": record,
}
(HERE / "candidate.json").write_text(
    json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(candidate, sort_keys=True))
