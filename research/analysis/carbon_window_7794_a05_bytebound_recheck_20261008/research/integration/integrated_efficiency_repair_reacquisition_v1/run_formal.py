#!/usr/bin/env python3
import json
from pathlib import Path
from common import compute, validate_fixture
R = Path(__file__).resolve().parent
f = json.loads((R/'fixture.json').read_text())
validate_fixture(f)
ratios = compute(f)
result = {
  "schema": "integrated_efficiency_repair_reacquisition_result_v1",
  "task": f["task"],
  "decision": "PASS_REPAIR_REACQUISITION_ACCOUNTING_SCOPED",
  "formal_invocation": 1,
  "formal_reruns": 0,
  "primary_comparator": f["primary_comparator"],
  "ratios": ratios,
  "persistent_repeat_B": f["persistent_repeat_B"],
  "secondary_context": f["secondary_context"],
  "interpretation": [
    "unit-specific ratios only; no synthetic scalar",
    "primary denominator is matched ephemeral task4/layout-B cold reacquisition",
    "different arms prevent causal same-arm repair-cost attribution",
    "repeat_B zero-model fields show restored future reuse but do not make repair itself free"
  ],
  "source_git_blob": f["source"]["git_blob"]
}
(R/'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps(result, sort_keys=True))
