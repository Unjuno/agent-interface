import json
import sys
from pathlib import Path

EXPECTED_VERSION = "codex-cli 0.146.1"
PASS = "PASS_INTERRUPT_CLOSED_PENDING_PROVIDER_STREAM_BEFORE_RELEASE"


def audit(result, process_exit, runner_exit):
    requests = result.get("mock_requests", [])
    events = result.get("mock_events", [])
    close_events = [row for row in events if row.get("event") in (
        "provider_socket_eof_before_release", "provider_socket_reset_before_release")]
    release_events = [row for row in events if row.get("event") == "response_release_gate_set"]
    requests_ok = (len(requests) == 1 and requests[0].get("path") == "/v1/responses" and
                   requests[0].get("peer_ip") == "127.0.0.1" and
                   isinstance(requests[0].get("body_sha256"), str) and
                   len(requests[0]["body_sha256"]) == 64 and
                   result.get("mock_listener_ip") == "127.0.0.1")
    close_ns = close_events[0].get("monotonic_ns", 0) if len(close_events) == 1 else 0
    release_ns = release_events[0].get("monotonic_ns", 0) if len(release_events) == 1 else 0
    request_ns = requests[0].get("received_monotonic_ns", 0) if len(requests) == 1 else 0
    sent_ns = result.get("interrupt_sent_at_ns", 0)
    ordering_ok = (len(close_events) == 1 and len(release_events) == 1 and
                   request_ns > 0 and request_ns < sent_ns <= close_ns < release_ns and
                   close_ns == result.get("provider_socket_close_at_ns") and
                   result.get("provider_socket_closed_before_release") is True and
                   result.get("provider_socket_close_kind_before_release") in ("eof", "reset"))
    checks = {
        "expected_cli_version": result.get("app_server_version") == EXPECTED_VERSION,
        "fresh_isolated_mock_request": result.get("pending_request_observed") is True and requests_ok,
        "no_user_credentials_passed": result.get("credentials_passed_to_app_server") is False,
        "interrupt_rpc_accepted": result.get("interrupt_rpc_accepted") is True and
            result.get("interrupt_rpc_error") is False,
        "provider_connection_closed_before_release": ordering_ok,
        "turn_completed_after_interrupt": isinstance(result.get("turn_completion_at_ns"), int) and
            result.get("turn_completion_at_ns", 0) >= sent_ns,
        "matching_turn_completed_interrupted": result.get("matching_turn_completion_observed") is True and
            result.get("completion_thread_matches") is True and
            result.get("completion_turn_matches") is True and
            result.get("turn_completion_status") == "interrupted",
        "one_request_no_mock_errors": result.get("mock_request_count") == 1 and
            result.get("mock_errors") == [],
        "processes_exit_zero": str(process_exit).strip() == "0" and
            str(runner_exit).strip() == "0" and result.get("app_server_exit_code") == 0,
        "reported_scoped_pass": result.get("disposition") == PASS,
    }
    return checks



def self_test():
    result = {
        "app_server_version": EXPECTED_VERSION,
        "pending_request_observed": True,
        "interrupt_sent_at_ns": 15,
        "turn_completion_at_ns": 25,
        "provider_socket_close_at_ns": 16,
        "mock_requests": [{"path": "/v1/responses", "peer_ip": "127.0.0.1",
                           "body_sha256": "a" * 64, "received_monotonic_ns": 10}],
        "mock_listener_ip": "127.0.0.1",
        "interrupt_rpc_accepted": True,
        "interrupt_rpc_error": False,
        "provider_socket_closed_before_release": True,
        "provider_socket_close_kind_before_release": "eof",
        "mock_events": [
            {"event": "provider_socket_eof_before_release", "monotonic_ns": 16},
            {"event": "response_release_gate_set", "monotonic_ns": 20}],
        "matching_turn_completion_observed": True,
        "completion_thread_matches": True,
        "completion_turn_matches": True,
        "turn_completion_status": "interrupted",
        "mock_request_count": 1, "mock_errors": [],
        "app_server_exit_code": 0,
        "credentials_passed_to_app_server": False,
        "disposition": PASS,
    }
    positive = audit(result, "0", "0")
    controls = {}
    mutations = {
        "closure_after_release_rejected": lambda r: (
            r.update(provider_socket_closed_before_release=False),
            r["mock_events"][0].update(monotonic_ns=30),
            r.update(provider_socket_close_at_ns=30),
            r["mock_events"][1].update(monotonic_ns=20)),
        "wrong_peer_rejected": lambda r: r["mock_requests"][0].update(peer_ip="192.0.2.1"),
        "credential_pass_rejected": lambda r: r.update(credentials_passed_to_app_server=True),
        "wrong_terminal_status_rejected": lambda r: r.update(turn_completion_status="completed"),
        "server_error_rejected": lambda r: r.update(mock_errors=["write_error"]),
    }
    for name, mutate in mutations.items():
        changed = json.loads(json.dumps(result))
        mutate(changed)
        controls[name] = not all(audit(changed, "0", "0").values())
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
    checks = audit(result,
                   (root / "process_exit.txt").read_text(encoding="ascii"),
                   (root / "runner_exit.txt").read_text(encoding="ascii"))
    report = {"disposition": "PASS_A01_AUDIT" if all(checks.values()) else "FAIL_A01_AUDIT",
              "checks": checks, "check_count": len(checks),
              "method_note": "EOF/reset is observed on the accepted loopback TCP socket before the response-release event; this does not establish remote provider inference or billing cancellation."}
    (root / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
