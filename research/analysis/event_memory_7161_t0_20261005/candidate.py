"""Project append-only event receipts into a typed continuation state."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "INPUT.json").read_text())
outputs = []
for case in data["cases"]:
    events = case["events"]
    kinds = [event["kind"] for event in events]
    observed = [e["value"] for e in events if e["kind"] in
                {"effect_observation", "external_change_observation"}]
    if "action_dispatch" not in kinds:
        state = "NOT_RUN"
    elif not observed:
        state = "PENDING"
    elif observed[-1] == "saved":
        state = "SUCCESS"
    elif observed[-1] == "unsaved" and "saved" in observed:
        state = "SUCCESS_THEN_REVERTED"
    else:
        state = "FAILED"
    outputs.append({"case_id": case["case_id"], "state": state,
                    "prediction_values": [e["value"] for e in events
                                          if e["kind"] == "effect_prediction"],
                    "observed_values": observed, "input_authority": False})
result = {"schema": "event-memory-result-v1", "outputs": outputs}
(HERE / "CANDIDATE.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
