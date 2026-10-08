"""Independent integrity and outcome classification for the retained A01 run."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
FROZEN = json.loads((ROOT / "FROZEN.json").read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_ns(value: object) -> bool:
    return type(value) is int and value > 0


checks = {
    "probe_sha256": sha(ROOT / "probe.py") == FROZEN["probe.py"],
    "test_sha256": sha(ROOT / "test_probe.py") == FROZEN["test_probe.py"],
    "fixture_sha256": sha(ROOT / "fixtures/v39-seq200.png") == FROZEN["fixtures/v39-seq200.png"],
    "schema_sha256": sha(ROOT / "protocol/turn_steer_user_input_schema.json") == FROZEN["protocol/turn_steer_user_input_schema.json"],
    "config_template_sha256": sha(ROOT / "CONFIG_TEMPLATE.toml") == FROZEN["CONFIG_TEMPLATE.toml"],
    "command_sha256": sha(ROOT / "COMMAND.txt") == FROZEN["COMMAND.txt"],
    "readme_sha256": sha(ROOT / "README.md") == FROZEN["README.md"],
    "auditor_sha256": sha(ROOT / "audit.py") == FROZEN["audit.py"],
    "candidate_source_sha256": sha(ROOT / "results/candidate_source.py") == FROZEN["results/candidate_source.py"],
}

raw = json.loads((ROOT / "results/candidate.stdout").read_text())
requests = raw.get("captured_requests")
image = (ROOT / "fixtures/v39-seq200.png").read_bytes()
data_url = "data:image/png;base64," + base64.b64encode(image).decode("ascii")
second = requests[1] if isinstance(requests, list) and len(requests) > 1 else {}
second_json = json.dumps(second, separators=(",", ":"))
text = FROZEN["observation_text"]

checks.update({
    "cli_version": raw.get("cli_version") == FROZEN["cli_version"],
    "configured_endpoint_loopback": isinstance(raw.get("mock_endpoint"), str)
        and raw["mock_endpoint"].startswith("http://127.0.0.1:"),
    "temporary_home": raw.get("temporary_codex_home") is True,
    "analytics_disabled": raw.get("analytics_disabled") is True,
    "active_regular_turn": raw.get("active_turn_status_before_steer") == "inProgress",
    "mock_request_list_valid": isinstance(requests, list),
    "captured_request_count_matches": isinstance(requests, list)
        and raw.get("mock_request_count") == len(requests),
    "png_identity": raw.get("image_sha256") == FROZEN["fixtures/v39-seq200.png"],
    "turn_completion_recorded": type(raw.get("turn_completed")) is bool,
    "response_one_accounted": type(raw.get("first_response_accounted")) is bool,
    "server_errors_list": isinstance(raw.get("server_errors"), list),
})

steer_reply = raw.get("steer_reply")
steer_accepted = isinstance(steer_reply, dict) and isinstance(steer_reply.get("result"), dict)
same_turn = bool(raw.get("initial_turn_id") and
                 raw.get("initial_turn_id") == raw.get("steer_turn_id"))
text_present = text in second_json
image_present = data_url in second_json
second_ns = raw.get("second_request_received_ns")
first_done_ns = raw.get("first_response_sent_ns")
release_ns = raw.get("first_response_release_ns")
if second_ns is None:
    order = "SECOND_REQUEST_NOT_OBSERVED"
elif not is_ns(second_ns):
    order = "ORDER_UNVERIFIABLE"
elif is_ns(first_done_ns):
    order = ("SECOND_REQUEST_WHILE_INITIAL_PENDING" if second_ns < first_done_ns
             else "SECOND_REQUEST_AFTER_INITIAL_COMPLETION")
elif is_ns(release_ns) and second_ns < release_ns:
    order = "SECOND_REQUEST_WHILE_INITIAL_PENDING"
else:
    order = "ORDER_UNVERIFIABLE"

release_delta = None
if is_ns(raw.get("steer_ack_ns")) and is_ns(release_ns):
    release_delta = release_ns - raw["steer_ack_ns"]
window_ok = release_delta is not None and 1_900_000_000 <= release_delta <= 2_200_000_000
checks["pending_window_bracket"] = window_ok
checks["order_label_matches_timestamps"] = order == raw.get("request_order")

exit_text = (ROOT / "results/candidate.exit").read_text().strip()
try:
    candidate_exit = int(exit_text)
    checks["candidate_exit_valid"] = candidate_exit in (0, 1)
except ValueError:
    candidate_exit = None
    checks["candidate_exit_valid"] = False

# Integrity only: scientific/hypothesis failure is recorded below, not treated as
# an auditor failure. Every gate retains its own disposition for honest reporting.
hard_checks = {key: value for key, value in checks.items() if key != "pending_window_bracket"}
integrity_ok = all(hard_checks.values())
disposition = "AUDIT_FAIL_INTEGRITY" if not integrity_ok else None
if disposition is None:
    if not steer_accepted:
        disposition = "FAIL_STEER_REJECTED"
    elif not same_turn:
        disposition = "FAIL_TURN_ID_MISMATCH"
    elif not text_present:
        disposition = "FAIL_OBSERVATION_TEXT_MISSING"
    elif not image_present:
        disposition = "FAIL_IMAGE_MISSING"
    elif not isinstance(requests, list) or len(requests) < 2:
        disposition = "FAIL_NO_FOLLOWUP"
    elif raw.get("server_errors"):
        disposition = "STOP_MOCK_OR_TRANSPORT_ERROR"
    elif raw.get("turn_completed") is not True:
        disposition = "STOP_TURN_INCOMPLETE"
    elif not window_ok:
        disposition = "STOP_PENDING_WINDOW_INVALID"
    elif order == "SECOND_REQUEST_WHILE_INITIAL_PENDING":
        disposition = "PASS_PREEMPTIVE_STEER"
    elif order == "SECOND_REQUEST_AFTER_INITIAL_COMPLETION":
        disposition = "FAIL_STEER_QUEUED"
    else:
        disposition = "STOP_ORDER_UNVERIFIABLE"

record = {
    "integrity_ok": integrity_ok,
    "checks": checks,
    "steer_accepted": steer_accepted,
    "same_turn_id": same_turn,
    "exact_observation_text_in_request_2": text_present,
    "exact_image_data_url_in_request_2": image_present,
    "candidate_exit": candidate_exit,
    "request_order_recomputed": order,
    "pending_window_after_ack_ns": release_delta,
    "pending_window_valid": window_ok,
    "disposition": disposition,
    "scope": "loopback mock only; no inference, real UI, device/game input, task effect, or MAP01 outcome",
}
(ROOT / "results/audit.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps(record, indent=2, sort_keys=True))
if not integrity_ok:
    raise SystemExit(1)
