import base64
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

EXPECTED_VERSION = "codex-cli 0.146.1"
MARKER = "UNTRUSTED CURRENT OBSERVATION: ammo=37"
PASS = "PASS_INTERRUPT_ADMITS_FRESH_OBSERVATION_BEFORE_HELD_RESPONSE_RELEASE"
PACKAGE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def png_is_valid_2x2_data_uri(value):
    prefix = "data:image/png;base64,"
    if not isinstance(value, str) or not value.startswith(prefix):
        return False
    try:
        data = base64.b64decode(value[len(prefix):], validate=True)
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            return False
        offset = 8
        chunks = []
        while offset < len(data):
            length = struct.unpack_from("!I", data, offset)[0]
            kind = data[offset + 4:offset + 8]
            payload = data[offset + 8:offset + 8 + length]
            crc = struct.unpack_from("!I", data, offset + 8 + length)[0]
            if zlib.crc32(kind + payload) & 0xffffffff != crc:
                return False
            chunks.append((kind, payload))
            offset += 12 + length
        ihdr = next(payload for kind, payload in chunks if kind == b"IHDR")
        width, height = struct.unpack_from("!II", ihdr)
        return width == 2 and height == 2 and chunks[-1][0] == b"IEND"
    except (ValueError, struct.error, StopIteration, zlib.error):
        return False


def audit(result, requests, app_exit, runner_exit, candidate_source, freeze):
    first_request = requests[0] if len(requests) > 0 else {}
    second_request = requests[1] if len(requests) > 1 else {}
    image_urls = second_request.get("observation_images", [])
    raw_request_at = second_request.get("request_monotonic")
    reported_request_at = result.get("second_request_at")
    source_order_ok = (
        "second_seen.wait(4)" in candidate_source and
        "release_first.set()" in candidate_source and
        candidate_source.index("second_seen.wait(4)") <
        candidate_source.index("release_first.set()")
    )
    checks = {
        "frozen_candidate_hash_matches": sha(PACKAGE / "run_a01.py") ==
            freeze.get("candidate", {}).get("sha256"),
        "expected_app_server_version": result.get("app_server_version") == EXPECTED_VERSION,
        "first_turn_interrupted": result.get("first_turn_status") == "interrupted",
        "second_turn_completed": result.get("second_turn_status") == "completed",
        "same_thread_distinct_turns": bool(result.get("thread_id")) and
            result.get("same_thread") is True and
            bool(result.get("first_turn_id")) and bool(result.get("second_turn_id")) and
            result.get("first_turn_id") != result.get("second_turn_id") and
            result.get("second_turn_thread_id") == result.get("thread_id"),
        "two_requests_reached_loopback_mock": len(requests) == 2 and
            result.get("requests_to_loopback_mock_only") == 2 and
            all(row.get("endpoint") == "POST /v1/responses" and
                row.get("loopback_peer") is True for row in requests),
        "fresh_request_precedes_release_by_event_barrier":
            result.get("second_request_before_first_response_release") is True and
            source_order_ok and isinstance(raw_request_at, (int, float)) and
            isinstance(reported_request_at, (int, float)) and
            0 <= reported_request_at - raw_request_at < 1.0,
        "fresh_request_contains_marker":
            second_request.get("observation_marker_present") is True and
            second_request.get("observation_text") == MARKER and
            result.get("second_request_contains_observation_text") is True,
        "fresh_request_contains_valid_2x2_png": len(image_urls) == 1 and
            png_is_valid_2x2_data_uri(image_urls[0]) and
            result.get("second_request_contains_valid_png") is True,
        "both_processes_exit_zero": str(app_exit).strip() == "0" and
            str(runner_exit).strip() == "0" and result.get("app_server_exit_code") == 0,
        "reported_disposition_pass": result.get("disposition") == PASS,
        "frozen_cli_identity_matches": freeze.get("app_server", {}).get("version") == EXPECTED_VERSION and
            freeze.get("app_server", {}).get("sha256") == sha(freeze.get("app_server", {}).get("path", "")),
    }
    return checks


def self_test():
    freeze = {"candidate": {"sha256": sha(PACKAGE / "run_a01.py")},
              "app_server": {"path": "/opt/homebrew/bin/codex",
                             "version": EXPECTED_VERSION,
                             "sha256": sha("/opt/homebrew/bin/codex")}}
    result = {
        "disposition": PASS, "app_server_version": EXPECTED_VERSION,
        "first_turn_status": "interrupted", "second_turn_status": "completed",
        "thread_id": "thread-a", "first_turn_id": "turn-a", "same_thread": True,
        "second_turn_thread_id": "thread-a", "second_turn_id": "turn-b",
        "requests_to_loopback_mock_only": 2,
        "second_request_before_first_response_release": True,
        "second_request_contains_observation_text": True,
        "second_request_contains_valid_png": True,
        "second_request_at": 2.0001, "app_server_exit_code": 0,
    }
    def chunk(kind, payload):
        return struct.pack("!I", len(payload)) + kind + payload + struct.pack(
            "!I", zlib.crc32(kind + payload) & 0xffffffff)
    ihdr = struct.pack("!2I5B", 2, 2, 8, 2, 0, 0, 0)
    raw = b"\x00" + bytes((10, 20, 30)) * 2 + b"\x00" + bytes((40, 50, 60)) * 2
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    request = {"request_index": 1, "endpoint": "POST /v1/responses",
               "loopback_peer": True, "request_monotonic": 2.0,
               "observation_marker_present": True, "observation_text": MARKER,
               "observation_images": ["data:image/png;base64," + base64.b64encode(png).decode()]}
    requests = [{"endpoint": "POST /v1/responses", "loopback_peer": True}, request]
    candidate_source = Path(PACKAGE / "run_a01.py").read_text(encoding="utf-8")
    positive = audit(result, requests, "0", "0", candidate_source, freeze)
    controls = {}
    mutations = {
        "completed_first_turn_rejected": lambda r, q: r.update(first_turn_status="completed"),
        "late_request_rejected": lambda r, q: r.update(second_request_before_first_response_release=False),
        "missing_marker_rejected": lambda r, q: q[1].update(observation_marker_present=False),
        "corrupt_png_rejected": lambda r, q: q[1].update(observation_images=["data:image/png;base64,AAAA"]),
        "non_loopback_peer_rejected": lambda r, q: q[1].update(loopback_peer=False),
    }
    for name, mutate in mutations.items():
        r = json.loads(json.dumps(result))
        q = json.loads(json.dumps(requests))
        mutate(r, q)
        controls[name] = not all(audit(r, q, "0", "0", candidate_source, freeze).values())
    if not all(positive.values()) or not all(controls.values()):
        raise SystemExit(json.dumps({"positive": positive, "controls": controls}, indent=2))
    print(json.dumps({"positive_checks": len(positive), "mutation_controls": controls,
                      "timestamp_note": "event barrier carries order; equal monotonic values are allowed"}, indent=2))


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_a01_v2.py --self-test | RESULTS_DIR")
    root = Path(sys.argv[1]).resolve()
    result = json.loads((root / "result.json").read_text(encoding="utf-8"))
    requests = json.loads((root / "requests_redacted.json").read_text(encoding="utf-8"))
    app_exit = (root / "process_exit.txt").read_text(encoding="ascii")
    runner_exit = (root / "runner_exit.txt").read_text(encoding="ascii")
    source = (PACKAGE / "run_a01.py").read_text(encoding="utf-8")
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    checks = audit(result, requests, app_exit, runner_exit, source, freeze)
    report = {
        "disposition": "PASS_A01_AUDIT_V2" if all(checks.values()) else "FAIL_A01_AUDIT_V2",
        "checks": checks,
        "method_note": "first_response_released_at was not retained because the server thread recorded it after result assembly. The strict event barrier is accepted only with the frozen runner source ordering second_seen.wait before release_first.set; the separate release timestamp is therefore unobserved.",
    }
    (root / "audit_v2.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
