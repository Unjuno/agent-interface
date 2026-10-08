#!/usr/bin/env python3
"""One hand-authored construction case, not the formal factorial run."""
import importlib.util
from pathlib import Path

source = Path(__file__).with_name("experiment.py")
spec = importlib.util.spec_from_file_location("alert_t4_experiment", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

all_alerts = module.run_stream("burst", 1, 3, "shifted", "EMIT_ALL")
safe = module.run_stream("burst", 1, 3, "shifted", "SAFE_IDENTITY_BATCH")
signature = module.run_stream("burst", 1, 3, "shifted", "SIGNATURE_BATCH")
score_only = module.run_stream("burst", 1, 3, "shifted", "PROBABILITY_THRESHOLD")
assert "a3-shift" not in safe["suppressed_ids"]
assert "a3-shift" in signature["suppressed_ids"]
assert "a3-shift" in score_only["suppressed_ids"]
assert "n1-copy" in safe["suppressed_ids"]
assert all_alerts["suppressed_ids"] == []
assert safe["suppressed_hard"] == 0
assert safe["actionable_missed_entities"] == all_alerts["actionable_missed_entities"]
print("construction smoke PASS: identity batching preserves shifted unique action and hard events")
