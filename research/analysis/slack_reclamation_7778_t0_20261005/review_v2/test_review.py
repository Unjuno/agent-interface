import copy
import importlib.util
import json
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("auditor_v2", root / "auditor_v2.py")
aud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aud)
base = json.loads((root / "review_v2/candidate.json").read_text())
inputs = json.loads((root / "review_v2/inputs.json").read_text())
aud.OUT = root / "review_v2"
assert aud.run_audit()["disposition"] == "PASS_METHOD_SCOPED"

def run(mutant):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d)
        (out / "inputs.json").write_text(json.dumps(inputs))
        (out / "candidate.json").write_text(json.dumps(mutant))
        aud.OUT = out
        return aud.run_audit()

m = copy.deepcopy(base)
row = next(x for x in m["rows"] if x["trace_id"] == "idle_gaps" and x["policy"] == "DEMAND_GUARDED_SLACK_STEAL")
event = next(e for e in row["events"] if e["action"] == "s0")
event["action"] = None
row["remaining"]["s0"] += 1
row["soft_service"] -= 1
r = run(m)
assert r["disposition"] == "FAIL_AUDIT", r["disposition"]

m = copy.deepcopy(base)
row = next(x for x in m["rows"] if x["trace_id"] == "burst_at_replenishment" and x["policy"] == "STATIC_RESERVATION")
row["soft_service"] = 0
r = run(m)
assert r["disposition"] == "FAIL_AUDIT", r["disposition"]
print("review-v2 regression checks: 2/2 rejected; baseline PASS_METHOD_SCOPED")
