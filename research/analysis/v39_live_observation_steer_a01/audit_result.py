"""Audit the frozen turn/steer result against raw mock request bytes."""

import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
frozen = json.loads((ROOT / "FROZEN.json").read_text())

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

for key, path in (("candidate_sha256", ROOT / "probe.py"),
                  ("test_sha256", ROOT / "test_probe.py"),
                  ("fixture_sha256", ROOT / "fixtures" / "v39-seq200.png")):
    assert sha(path) == frozen[key], f"frozen hash mismatch: {path.name}"
for name, expected in frozen["schema_sha256"].items():
    assert sha(ROOT / "schema" / name) == expected, f"schema hash mismatch: {name}"
legacy_schema = json.loads((ROOT / "schema/codex-cli-0.146.1-ClientRequest.json").read_text())
modern_schema = json.loads((ROOT / "schema/codex-cli-0.160.0-ClientRequest.json").read_text())
legacy_start = legacy_schema["definitions"]["TurnStartParams"]["properties"]
legacy_steer = legacy_schema["definitions"]["TurnSteerParams"]
modern_start = modern_schema["definitions"]["TurnStartParams"]["properties"]
assert "toolOutput" not in legacy_start
assert set(frozen["rpc_required_fields"]) <= set(legacy_steer["required"])
assert "toolOutput" in modern_start
legacy_input_types = {
    choice["properties"]["type"]["enum"][0]
    for choice in legacy_schema["definitions"]["UserInput"]["oneOf"]
}
assert {"text", "image"} <= legacy_input_types

stdout = (ROOT / "results" / "candidate.stdout").read_bytes()
assert stdout == (ROOT / "results" / "candidate.json").read_bytes()
result = json.loads(stdout)
exit_code = int((ROOT / "results" / "candidate.exit").read_text().strip())
requests = result["mock_request_bodies"]
raw_bodies = result["mock_request_body_base64"]
raw_hashes = result["mock_request_body_sha256"]
assert len(requests) == result["mock_request_count"]
assert len(raw_bodies) == len(raw_hashes) == len(requests)
for parsed, encoded, expected_hash in zip(requests, raw_bodies, raw_hashes):
    raw = base64.b64decode(encoded, validate=True)
    assert hashlib.sha256(raw).hexdigest() == expected_hash
    assert json.loads(raw) == parsed

assert result["cli_version"] == frozen["cli_version"]
assert result["loopback_only"] is True and result["temporary_codex_home"] is True
assert result["codex_bin_path"] == str((ROOT / frozen["cli_path"]).resolve())
assert result["api_key_env_cleared"] is True
assert result["steer_accepted"] == (result["external_turn_id"] is not None)
assert bool(result["initial_turn_id"])
assert result["same_turn_id"] == (result["initial_turn_id"] == result["external_turn_id"])
assert result["initial_turn_status_at_start"] == "inProgress"
assert result["first_response_release_ns"] > result["external_ack_ns"]
assert result["first_request_received_ns"] < result["external_ack_ns"]
assert 1_900_000_000 <= result["first_response_release_ns"] - result["external_ack_ns"] <= 2_300_000_000

second = requests[1] if len(requests) > 1 else {}
second_wire = json.dumps(second, separators=(",", ":"))
frame = (ROOT / "fixtures" / "v39-seq200.png").read_bytes()
image_url = "data:image/png;base64," + base64.b64encode(frame).decode("ascii")
text_present = frozen["observation_text"] in second_wire
image_present = image_url in second_wire
assert result["text_delivered"] == text_present
assert result["image_delivered"] == image_present
assert result["observation_in_second_request"] == text_present
assert result["image_in_second_request"] == image_present
assert result["frame_sha256_expected"] == frozen["fixture_sha256"]
assert result["image_sha256"] == frozen["fixture_sha256"]

second_ns = result["second_request_received_ns"]
first_done_ns = result["first_response_sent_ns"]
if second_ns is None or first_done_ns is None:
    computed_order = "ORDER_UNVERIFIABLE" if second_ns is not None else "SECOND_REQUEST_NOT_OBSERVED"
elif second_ns < first_done_ns:
    computed_order = "SECOND_REQUEST_WHILE_INITIAL_PENDING"
else:
    computed_order = "SECOND_REQUEST_AFTER_INITIAL_COMPLETION"
assert result["request_order"] == computed_order

candidate_gate = all((
    result["initialize_ok"], result["thread_started"], result["steer_accepted"],
    result["same_turn_id"], result["initial_turn_status_at_start"] == "inProgress",
    result["turn_completed"], text_present, image_present, first_done_ns is not None,
    not result["server_errors"], len(requests) >= 2,
))
assert (exit_code == 0) == candidate_gate

summary = {
    "audit": "PASS_RETAINED_TURN_STEER_RESULT",
    "candidate_gate": "PASS_TURN_STEER_DELIVERY" if candidate_gate else "STOP_OR_DELIVERY_FAILURE_RETAINED",
    "candidate_exit": exit_code,
    "same_turn_id": result["same_turn_id"],
    "text_delivered": text_present,
    "image_delivered": image_present,
    "request_order": computed_order,
    "mock_request_count": len(requests),
    "server_errors": result["server_errors"],
}
print(json.dumps(summary, indent=2, sort_keys=True))
