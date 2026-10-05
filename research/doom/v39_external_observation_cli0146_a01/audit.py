#!/usr/bin/env python3
"""Independent raw-request audit for the CLI 0.146.1 probe pair."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parent
FRAME_SHA256 = "0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c"
EVENT_TEXT = "Fresh observation seq=200; HUD health 51, ammo 38."


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_manifest() -> tuple[bool, int]:
    repo_root = ROOT.parents[2]
    rows = (ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    valid = True
    for row in rows:
        expected, relative = row.split("  ", 1)
        path = repo_root / relative
        valid = valid and path.is_file() and digest(path.read_bytes()) == expected
    return valid, len(rows)


def load(name: str) -> dict:
    return json.loads((ROOT / "raw" / name).read_text(encoding="utf-8"))


def audit_case(name: str, expected_requests: int, original_done: bool,
               external_done: bool, original_done_before: bool) -> dict:
    data = load(name)
    requests = data["mock_request_bodies"]
    request_wire = json.dumps(requests, separators=(",", ":"))
    image_data = "data:image/png;base64," + base64.b64encode(
        (ROOT.parents[0] / "results/map01-v39-coast-liveness-live-01/runtime/200.png").read_bytes()
    ).decode("ascii")
    outputs = [
        item
        for request in requests
        for item in request.get("input", [])
        if isinstance(item, dict) and item.get("type") == "function_call_output"
    ]
    output_wire = json.dumps(outputs, separators=(",", ":"))
    same_turn = data.get("initial_turn_id") == data.get("external_turn_id")
    checks = {
        "cli_version_0146_1": data.get("cli_version") == "codex-cli 0.146.1",
        "loopback_and_temp_home": data.get("loopback_only") is True and data.get("temporary_codex_home") is True,
        "external_turn_accepted": data.get("external_turn_accepted") is True,
        "distinct_turn_ids": bool(data.get("initial_turn_id")) and bool(data.get("external_turn_id")) and not same_turn,
        "request_count": len(requests) == expected_requests == data.get("mock_request_count"),
        "observation_not_in_responses_input": EVENT_TEXT not in request_wire and EVENT_TEXT not in output_wire,
        "image_not_in_responses_input": image_data not in request_wire and image_data not in output_wire,
        "no_input_image_items": data.get("input_image_count") == 0,
        "independent_request_hash": data.get("all_mock_input_sha256") == digest(request_wire.encode("utf-8")),
        "runner_request_types_match": data.get("request_input_types") == [
            [item.get("type") for item in request.get("input", []) if isinstance(item, dict)]
            for request in requests
        ],
        "server_error_free": data.get("server_errors") == [],
        "completion_shape": data.get("original_turn_completed") is original_done
        and data.get("external_turn_completed") is external_done,
        "precondition_timing": data.get("original_turn_completed_before_external_message") is original_done_before,
    }
    if name == "during-turn.json":
        checks["one_request_and_external_still_incomplete"] = len(requests) == 1 and not external_done
        checks["external_ack_precedes_initial_response_release"] = (
            data.get("first_mock_request_seen_monotonic_ns")
            <= data.get("external_message_sent_monotonic_ns")
            <= data.get("external_message_ack_monotonic_ns")
            <= data.get("initial_response_released_monotonic_ns")
            and data.get("ack_while_initial_response_pending") is True
            and 1_900_000_000 <= (
                data.get("initial_response_released_monotonic_ns")
                - data.get("external_message_ack_monotonic_ns")
            ) <= 3_000_000_000
        )
    else:
        checks["separate_followup_request"] = len(requests) == 2 and external_done
        checks["initial_response_released_before_external_message"] = (
            data.get("first_mock_request_seen_monotonic_ns")
            <= data.get("initial_response_released_monotonic_ns")
            <= data.get("external_message_sent_monotonic_ns")
            <= data.get("external_message_ack_monotonic_ns")
            and data.get("ack_while_initial_response_pending") is False
        )
    return {
        "file": name,
        "checks": checks,
        "pass": all(checks.values()),
        "mock_request_count": len(requests),
        "request_sha256": [digest(json.dumps(r, separators=(",", ":")).encode()) for r in requests],
        "all_mock_input_sha256": digest(request_wire.encode("utf-8")),
        "initial_turn_id": data.get("initial_turn_id"),
        "external_turn_id": data.get("external_turn_id"),
        "server_errors": data.get("server_errors"),
    }


def main() -> int:
    frame = ROOT.parents[0] / "results/map01-v39-coast-liveness-live-01/runtime/200.png"
    frame_ok = digest(frame.read_bytes()) == FRAME_SHA256
    manifest_ok, manifest_entries = verify_manifest()
    result = {
        "audit_kind": "offline-local-mock-protocol-audit",
        "frame_sha256_expected": FRAME_SHA256,
        "frame_hash_ok": frame_ok,
        "manifest_ok": manifest_ok,
        "manifest_entries": manifest_entries,
        "cases": [
            audit_case("during-turn.json", 1, True, False, False),
            audit_case("after-turn.json", 2, True, True, True),
        ],
    }
    result["pass"] = frame_ok and manifest_ok and all(case["pass"] for case in result["cases"])
    (ROOT / "raw/audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
