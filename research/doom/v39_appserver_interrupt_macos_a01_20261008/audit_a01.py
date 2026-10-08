import base64
import json
import struct
import sys
import zlib
from pathlib import Path

EXPECTED_VERSION = "codex-cli 0.146.1"
MARKER = "UNTRUSTED CURRENT OBSERVATION: ammo=37"
PASS = "PASS_INTERRUPT_ADMITS_FRESH_OBSERVATION_BEFORE_HELD_RESPONSE_RELEASE"


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


def audit(result, requests, app_exit, runner_exit):
    first = result.get("first_response_released_at")
    second = result.get("second_request_at")
    second_body = json.dumps(requests[1].get("body", {})) if len(requests) > 1 else ""
    second_input = requests[1].get("body", {}).get("input", []) if len(requests) > 1 else []
    images = [item.get("url") for item in second_input
              if isinstance(item, dict) and item.get("type") == "image"]
    checks = {
        "expected_app_server_version": result.get("app_server_version") == EXPECTED_VERSION,
        "first_turn_interrupted": result.get("first_turn_status") == "interrupted",
        "second_turn_completed": result.get("second_turn_status") == "completed",
        "same_thread_distinct_turns": bool(result.get("thread_id")) and
            result.get("same_thread") is True and
            bool(result.get("first_turn_id")) and bool(result.get("second_turn_id")) and
            result.get("first_turn_id") != result.get("second_turn_id") and
            result.get("second_turn_thread_id") == result.get("thread_id"),
        "exactly_two_mock_responses_requests": len(requests) == 2 and
            result.get("requests_to_loopback_mock_only") == 2 and
            all(row.get("path", "").endswith("/responses") and
                row.get("client_address", [None])[0] == "127.0.0.1" for row in requests),
        "fresh_request_before_release_barrier":
            result.get("second_request_before_first_response_release") is True and
            isinstance(first, (int, float)) and isinstance(second, (int, float)) and
            second <= first,
        "request_contains_exact_text_marker": MARKER in second_body and
            result.get("second_request_contains_observation_text") is True,
        "request_contains_valid_2x2_png": len(images) == 1 and
            png_is_valid_2x2_data_uri(images[0]) and
            result.get("second_request_contains_valid_png") is True,
        "app_server_and_runner_exit_zero": str(app_exit).strip() == "0" and
            str(runner_exit).strip() == "0" and result.get("app_server_exit_code") == 0,
        "reported_disposition_pass": result.get("disposition") == PASS,
    }
    return checks


def self_test():
    result = {
        "disposition": PASS, "app_server_version": EXPECTED_VERSION,
        "first_turn_status": "interrupted", "second_turn_status": "completed",
        "thread_id": "thread-a", "first_turn_id": "turn-a", "same_thread": True,
        "second_turn_thread_id": "thread-a", "second_turn_id": "turn-b",
        "requests_to_loopback_mock_only": 2,
        "second_request_before_first_response_release": True,
        "second_request_contains_observation_text": True,
        "second_request_contains_valid_png": True,
        "first_response_released_at": 2.0, "second_request_at": 2.0,
        "app_server_exit_code": 0,
    }
    # Use a valid chunked PNG for the positive fixture.
    def chunk(kind, payload):
        return struct.pack("!I", len(payload)) + kind + payload + struct.pack(
            "!I", zlib.crc32(kind + payload) & 0xffffffff)
    ihdr = struct.pack("!2I5B", 2, 2, 8, 2, 0, 0, 0)
    raw = b"\x00" + bytes((10, 20, 30)) * 2 + b"\x00" + bytes((40, 50, 60)) * 2
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    valid_png = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    requests = [
        {"path": "/v1/responses", "client_address": ["127.0.0.1", 1234],
         "body": {"input": "initial"}},
        {"path": "/v1/responses", "client_address": ["127.0.0.1", 1235],
         "body": {"input": [
            {"type": "text", "text": MARKER}, {"type": "image", "url": valid_png}]}}
    ]
    positive = audit(result, requests, "0", "0")
    controls = {}
    for name, mutate in {
        "completed_first_turn_rejected": lambda r, q: r.update(first_turn_status="completed"),
        "late_request_rejected": lambda r, q: (r.update(second_request_before_first_response_release=False),
                                                 r.update(second_request_at=3.0)),
        "missing_text_rejected": lambda r, q: q[1]["body"]["input"][0].update(text="missing"),
        "missing_image_rejected": lambda r, q: q[1]["body"]["input"].pop(),
        "bad_exit_rejected": lambda r, q: r.update(app_server_exit_code=1),
    }.items():
        candidate_result = json.loads(json.dumps(result))
        candidate_requests = json.loads(json.dumps(requests))
        mutate(candidate_result, candidate_requests)
        controls[name] = not all(audit(candidate_result, candidate_requests,
                                       "1" if name == "bad_exit_rejected" else "0", "0").values())
    if not all(positive.values()) or not all(controls.values()):
        raise SystemExit(json.dumps({"positive": positive, "controls": controls}, indent=2))
    print(json.dumps({"positive_checks": len(positive), "mutation_controls": controls}, indent=2))


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_a01.py --self-test | RESULTS_DIR")
    root = Path(sys.argv[1]).resolve()
    result = json.loads((root / "result.json").read_text(encoding="utf-8"))
    requests = json.loads((root / "requests.json").read_text(encoding="utf-8"))
    app_exit = (root / "process_exit.txt").read_text(encoding="ascii")
    runner_exit = (root / "runner_exit.txt").read_text(encoding="ascii")
    checks = audit(result, requests, app_exit, runner_exit)
    report = {"disposition": "PASS_A01_AUDIT" if all(checks.values()) else "FAIL_A01_AUDIT",
              "checks": checks, "check_count": len(checks)}
    (root / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
