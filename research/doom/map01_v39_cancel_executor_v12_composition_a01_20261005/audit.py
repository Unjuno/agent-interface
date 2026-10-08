"""Independent structural audit of the saved one-shot event output."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "results/formal_04/candidate.json").read_text(encoding="utf-8"))
events = data["events"]
assert data["schema"] == "map01-v39-cancel-executor-v12-composition-candidate-v1"
rid = "v13-v12-a01"
rows = [(i, e) for i, e in enumerate(events) if e.get("id") == rid]
per_key = [(i, e) for i, e in rows if e.get("event") == "input_release_measurement"]
aggregate = [(i, e) for i, e in rows if e.get("event") == "input_released"]
terminals = [(i, e) for i, e in rows if e.get("event") == "terminal"]
assert len(per_key) == len(aggregate) == len(terminals) == 1
pi, p = per_key[0]
ai, a = aggregate[0]
ti, terminal = terminals[0]
m = p["physical_key_measurement"]
assert p["step"] == 0 and p["key"] == "F8" and p["reason"] == "cancelled"
assert p["intent_token"] == "intent-v13-v12-a01"
assert m["classification"] == "CONFIRMED_PHYSICAL_UP"
assert m["identity_status"] == "RETIRED" and m["actuation_id"]
assert m["adapter_edge"]["grants_input_authority"] is False
assert a["owner_release"]["verified"] is True
assert a["owner_release"]["keys_down"] == [] and a["owner_release"]["buttons_down"] == []
assert a["grants_input_authority"] is False
assert max(pi, ai) < ti
assert terminal["status"] == "cancelled"
assert data["fake_physical_keys"] == data["backend_held"] == []
assert data["executor_active"] is False and data["executor_release_errors"] == {}
assert all(e.get("grants_input_authority") is not True for e in events)
report = {"status": "PASS_EXECUTOR_V12_COMPOSITION_SCOPED", "per_key_release_index": pi,
          "aggregate_release_index": ai, "terminal_index": ti, "event_count": len(events),
          "actuation_id": m["actuation_id"], "scope": "synthetic fake-display construction only"}
(HERE / "results/formal_04/audit.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
