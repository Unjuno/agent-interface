import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research" / "live_control"))
sys.path.insert(0, str(ROOT / "research" / "doom"))
from candidate import assess_pair
from test_candidate import fixture, naive_a02_compose

HERE = Path(__file__).resolve().parent
out = HERE / "RESULT.json"
if out.exists():
    raise SystemExit("refusing to overwrite retained result")
data = fixture()
rows = []
for case in data["cases"]:
    result = assess_pair(data["source_event"], case["event"])
    rows.append({"name": case["name"], "expected": case["decision"], "result": result})
split = next(c["event"] for c in data["cases"] if c["name"] == "signal_sequence_skew")
naive = naive_a02_compose(data["source_event"], split)
payload = {"schema": "a03-paired-epoch-probe-v1", "mode": "offline-construction",
           "rows": rows, "a02_split_epoch_control": naive,
           "all_expected": all(r["expected"] == r["result"]["decision"] for r in rows),
           "grants_input_authority": False}
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"result": str(out), "all_expected": payload["all_expected"],
                  "cases": len(rows)}, sort_keys=True))
