"""Independent raw-evidence audit for interval-censored T3 composition."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "run"
manifest = json.loads((ROOT / "T3_FILES.sha256.json").read_text(encoding="utf-8"))
for entry in manifest["files"]:
    content = (ROOT / entry["path"]).read_bytes()
    assert len(content) == entry["bytes"]
    assert hashlib.sha256(content).hexdigest() == entry["sha256"], entry["path"]
spec = importlib.util.spec_from_file_location("candidate_adapter", ROOT / "adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
from producer_input_edge_receipts import input_edge_receipts

raw_path = RUN / "a01-input-edge-receipt.jsonl"
raw_bytes = raw_path.read_bytes()
freeze = json.loads((ROOT / "T3_FREEZE.json").read_text(encoding="utf-8"))
projection_bytes = (ROOT / freeze["input_producer"]["projection_snapshot_path"]).read_bytes()
assert hashlib.sha256(projection_bytes).hexdigest() == freeze["input_producer"]["projection_snapshot_sha256"]
assert hashlib.sha256(raw_bytes).hexdigest() == freeze["raw_fixture"]["receipt_export_sha256"]
receipts = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines() if line]
assert len(receipts) == freeze["raw_fixture"]["adapter_receipt_count"] == 1
assert all(row["status"] in {"adapter_edge_brackets_paired",
                              "adapter_edge_receipt_incomplete"} for row in receipts)
assert receipts[0]["program_id_sha256"] == freeze["identity_hashes"]["program_id_sha256"]
assert receipts[0]["intent_token_sha256"] == freeze["identity_hashes"]["intent_token_sha256"]
assert receipts[0]["owner_id_sha256"] == freeze["identity_hashes"]["owner_id_sha256"]
source_path = RUN / "a01-input-source-events.jsonl"
source_bytes = source_path.read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == freeze["raw_fixture"]["source_events_sha256"]
source_events = [json.loads(line) for line in source_bytes.decode("utf-8-sig").splitlines() if line]
regenerated = input_edge_receipts(source_events)
assert regenerated == receipts, (regenerated, receipts)
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
        dict(receipt, intent_token_sha256="a" * 64),
        dict(receipt, program_id_sha256="b" * 64, key="a",
             intent_token_sha256="c" * 64, owner_id_sha256="d" * 64),
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
                  "source_events_sha256": hashlib.sha256(source_bytes).hexdigest(),
                  "retained_source_export_sha256": freeze["raw_fixture"]["source_export_sha256"],
                  "scenario_count": len(cases), "errors": []}, indent=2, sort_keys=True))
