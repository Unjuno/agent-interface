"""Black-box construction controls for #5666; not a raw-only independent audit."""

import importlib.util
import json
from pathlib import Path


SOURCE = Path(__file__).with_name("check.py")
if not SOURCE.exists():
    SOURCE = Path(__file__).with_name("issue5666_trace_reduction_t1_construction.py")
spec = importlib.util.spec_from_file_location("candidate_5666", SOURCE)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)

cases = [
    ("original", ("setup", "noise", "observe", "grant", "act", "release"), True,
     (1, ("WRONG_TARGET_EFFECT", "act", "wrong-target"))),
    ("remove_noise", ("setup", "observe", "grant", "act", "release"), True,
     (1, ("WRONG_TARGET_EFFECT", "act", "wrong-target"))),
    ("grant_missing", ("setup", "observe", "act", "release"), False,
     (1, ("AUTHORITY_OR_SETUP_GAP", "act", "no-effect"))),
    ("release_missing", ("setup", "observe", "grant", "act"), False,
     (1, ("HELD_INPUT_LEAK", "release", "unknown-effect"))),
    ("act_before_grant", ("setup", "observe", "act", "grant", "release"), False,
     (1, ("WRONG_TARGET_EFFECT", "act", "wrong-target"))),
    ("duplicate_observation", ("setup", "observe", "observe", "grant", "act", "release"), False,
     (1, ("WRONG_TARGET_EFFECT", "act", "wrong-target"))),
    ("unknown_node", ("setup", "observe", "grant", "unknown", "act", "release"), False,
     (1, ("WRONG_TARGET_EFFECT", "act", "wrong-target"))),
    ("no_action", ("setup", "observe", "grant", "release"), False,
     (0, ("NO_ACTION", None, None))),
]

results = []
for name, trace, expected_legal, expected_outcome in cases:
    actual_legal = candidate.legal(trace)
    actual_outcome = candidate.simulate(trace)
    passed = actual_legal == expected_legal and actual_outcome == expected_outcome
    results.append({"name": name, "pass": passed})

print(json.dumps({"scope": "host-only black-box construction controls; not raw-only audit",
                  "cases": results, "all_pass": all(x["pass"] for x in results)}, indent=2))
if not all(x["pass"] for x in results):
    raise SystemExit(1)

