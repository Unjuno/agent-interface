"""Independently check the frozen A03 candidate record."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
frozen = json.loads((ROOT / "FROZEN.json").read_text())
result_path = ROOT / "results" / "candidate.json"
stdout = (ROOT / "results" / "candidate.stdout").read_bytes()
assert hashlib.sha256((ROOT / "probe.py").read_bytes()).hexdigest() == frozen["candidate_sha256"]
assert hashlib.sha256((ROOT / "test_probe.py").read_bytes()).hexdigest() == frozen["test_sha256"]
assert hashlib.sha256((ROOT / "fixtures" / "v39-seq200.png").read_bytes()).hexdigest() == frozen["fixture_sha256"]
assert hashlib.sha256(stdout).hexdigest() == hashlib.sha256(result_path.read_bytes()).hexdigest()
assert (ROOT / "results" / "candidate.exit").read_text().strip() in {"0", "1"}
result = json.loads(result_path.read_text())
assert result["cli_version"] == frozen["cli_version"]
assert result["loopback_only"] and result["temporary_codex_home"]
assert result["initial_turn_id"] == result["external_turn_id"]
assert result["external_turn_status_at_ack"] == "inProgress"
assert result["first_response_sent_ns"] is not None
assert result["request_order"] in frozen["decision_labels"]
assert result["second_request_received_ns"] > result["first_response_sent_ns"]
assert result["first_response_sent_ns"] > result["first_response_release_ns"]
assert result["first_response_release_ns"] > result["external_ack_ns"]
assert 1_900_000_000 <= result["first_response_release_ns"] - result["external_ack_ns"] <= 2_200_000_000
assert result["request_order"] == "SECOND_REQUEST_AFTER_INITIAL_COMPLETION"
assert not result["second_request_before_release_gate"]
assert result["mock_request_count"] >= 2
assert result["observation_in_second_request"] and result["image_in_second_request"]
assert result["turn_completed"] and not result["server_errors"]
assert (ROOT / "results" / "candidate.stderr").exists()
print(json.dumps({
    "audit": "PASS_RETAINED_PROTOCOL_ORDERING_RESULT",
    "request_order": result["request_order"],
    "first_response_sent_ns": result["first_response_sent_ns"],
    "second_request_received_ns": result["second_request_received_ns"],
    "second_request_delay_after_response_ms": round(
        (result["second_request_received_ns"] - result["first_response_sent_ns"]) / 1_000_000, 3
    ),
    "candidate_exit": (ROOT / "results" / "candidate.exit").read_text().strip(),
}, indent=2, sort_keys=True))
