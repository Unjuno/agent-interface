from __future__ import annotations
import csv, hashlib, json, statistics, sys
from pathlib import Path

root = Path(__file__).resolve().parent
raw = root / "results" / "raw.csv"
machine = json.loads((root / "results" / "machine.json").read_text(encoding="utf-8"))
freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8-sig"))
source = root / "quantum_probe.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == machine["candidate_source_sha256"]
assert hashlib.sha256(raw.read_bytes()).hexdigest() == machine["raw_csv_sha256"]
with raw.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
lat = [r for r in rows if r["kind"] == "latency"]
idle = [r for r in rows if r["kind"] == "idle"]
assert len(lat) == 256 and len(idle) == 140
by = {arm: {int(r["pair"]): r for r in lat if r["arm"] == arm} for arm in ("1ms", "5ms")}
assert all(len(by[a]) == 128 for a in by)
assert all(r["payload_ok"] == "True" for r in lat)
assert set(by["1ms"]) == set(by["5ms"])
assert machine.get("eof_smoke") == {"1ms_eof": True, "5ms_eof": True}
for pair in by["1ms"]:
    assert by["1ms"][pair]["delay_ms"] == by["5ms"][pair]["delay_ms"]
    assert float(by["1ms"][pair]["quantum_ms"]) == 1.0
    assert float(by["5ms"][pair]["quantum_ms"]) == 5.0
improvements = [float(by["5ms"][i]["latency_ms"]) - float(by["1ms"][i]["latency_ms"]) for i in by["1ms"]]
def percentile(values, p):
    s=sorted(values); k=(len(s)-1)*p; lo=int(k); hi=min(lo+1,len(s)-1); return s[lo]+(s[hi]-s[lo])*(k-lo)
idle_summary={}
for arm in ("1ms","5ms"):
    ar=[r for r in idle if r["arm"]==arm]
    assert len(ar)==70 and all(r["timed_out"]=="True" for r in ar)
    cpu=sum(float(r["cpu_ms"]) for r in ar); wall=sum(float(r["wall_ms"]) for r in ar)
    idle_summary[arm]={"trials":len(ar),"cpu_ms":cpu,"wall_ms":wall,"cpu_percent":100*cpu/wall}
rule=freeze["decision_rule"]
keep=percentile(improvements,.95)>=1.0 and idle_summary["1ms"]["cpu_percent"] < 1.0
summary={"latency_trials_per_arm":128,"paired_p95_improvement_ms":percentile(improvements,.95),"paired_median_improvement_ms":statistics.median(improvements),"latency_1ms_p95_ms":percentile([float(r["latency_ms"]) for r in by["1ms"].values()],.95),"latency_5ms_p95_ms":percentile([float(r["latency_ms"]) for r in by["5ms"].values()],.95),"idle":idle_summary,"decision":"KEEP_1MS" if keep else "HOLD","all_validity_gates_passed":True,"decision_rule":rule}
(root/"results"/"RESULT.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,indent=2))
