"""Independent raw-evidence audit for interval-censored T3 composition."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "run"
spec = importlib.util.spec_from_file_location("candidate_adapter", ROOT / "adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

raw_path = RUN / "a01-input-edge-receipt.jsonl"
raw_bytes = raw_path.read_bytes()
freeze = json.loads((ROOT / "T3_FREEZE.json").read_text(encoding="utf-8"))
assert hashlib.sha256(raw_bytes).hexdigest() == freeze["raw_fixture"]["receipt_export_sha256"]
receipts = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines() if line]
assert len(receipts) == freeze["raw_fixture"]["adapter_receipt_count"] == 2
assert all(row["event"] == "input_edge_receipt" for row in receipts)
receipt = receipts[0]
samples = [
    {"controller_visible": False, "payload": {
        "schema": "independent-progress-sample-v2", "sample_ns": 87811364892000,
        "kill_count": 0, "death_count": 0, "episode_finished": False,
        "player_dead": False, "map_exit": False}},
    {"controller_visible": False, "payload": {
        "schema": "independent-progress-sample-v2", "sample_ns": 87811364948000,
        "kill_count": 1, "death_count": 0, "episode_finished": False,
        "player_dead": False, "map_exit": False}},
]
event = {"schema": "independent-progress-event-v2", "event_sequence": 1,
         "observed_ns": 87811364948000, "kind": "KILL_COUNT_INCREASE",
         "polarity": "positive", "useful": True, "controller_visible": False,
         "before": {"kill_count": 0}, "after": {"kill_count": 1, "delta": 1}}
cases = {
    "single_retained_envelope": [receipt],
    "two_possible_intents": [
        dict(receipt, intent_token_sha256="token-a"),
        dict(receipt, id="cover-8", intent_token_sha256="token-b",
             owner_id_sha256="owner-2"),
    ],
}
expected = {"single_retained_envelope": "UNRESOLVED",
            "two_possible_intents": "AMBIGUOUS"}
for name, rows in cases.items():
    actual = adapter.adapt_session_records(samples, [event], rows)
    retained = json.loads((RUN / f"{name}.json").read_text(encoding="utf-8"))
    assert actual == retained, (name, actual, retained)
    assert actual["trace_integrity"] == "MEASURED_INTERVALS_ONLY"
    assert actual["attributions"][0]["status"] == expected[name]
    assert actual["attributions"][0]["intent_token"] is None
    assert actual["attributions"][0]["causal_attribution"] == "NOT_ESTABLISHED"
print(json.dumps({"audit": "PASS_INTERVAL_CENSORED_COMPOSITION_SCOPED",
                  "raw_receipts_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                  "retained_source_export_sha256": freeze["raw_fixture"]["source_export_sha256"],
                  "scenario_count": len(cases), "errors": []}, indent=2, sort_keys=True))
