"""Conservatively account for the observed Windows monotonic clock resolution."""
import json,time
from pathlib import Path
p=Path(__file__).resolve().parent
a=json.loads((p/"audit_followup.json").read_text(encoding="utf-8"))
t=a["timing"]
q=round(time.get_clock_info("monotonic").resolution*1_000_000_000)
d=t["effect_to_oracle_observation_interval_ns"]["lower_bound_ns"]
t["clock_implementation"]=time.get_clock_info("monotonic").implementation
t["clock_quantum_ns"]=q
t["effect_to_oracle_observation_quantized_interval_ns"]=[max(0,d-q),d+q]
t["effect_to_oracle_observation_quantized_interval_ms"]=[max(0,d-q)/1_000_000,(d+q)/1_000_000]
t["save_write_elapsed_upper_bound_ns_when_readings_equal"]=q
t["note"]="GetTickCount64-backed monotonic_ns readings are quantized; the raw delta is not exact. The interval expands by one reported clock quantum for the difference of two timestamps."
a["schema"]="win32-task-effect-timing-r38d-additive-audit-v2"
a["limitations"].append("clock is GetTickCount64-backed with reported 15.625 ms resolution; timing delta expanded by one clock quantum")
(p/"audit_followup_v3.json").write_text(json.dumps(a,sort_keys=True,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"clock":t["clock_implementation"],"quantum_ns":q,"effect_oracle_latency_ms":t["effect_to_oracle_observation_quantized_interval_ms"]},indent=2))
