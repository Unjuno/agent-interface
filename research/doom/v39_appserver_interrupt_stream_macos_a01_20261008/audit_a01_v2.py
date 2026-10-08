import hashlib
import json
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
EXPECTED_VERSION = "codex-cli 0.146.1"
OBSERVED_FAIL = "FAIL_STREAM_NOT_CLOSED_BEFORE_RELEASE"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(result, process_exit, runner_exit, stderr_summary, freeze):
    requests = result.get("mock_requests", [])
    events = result.get("mock_events", [])
    close_events = [row for row in events if row.get("event") in (
        "provider_socket_eof_before_release", "provider_socket_reset_before_release")]
    release_events = [row for row in events if row.get("event") == "response_release_gate_set"]
    open_events = [row for row in events if row.get("event") == "mock_response_created_sent"]
    request_events = [row for row in events if row.get("event") == "responses_request_received"]
    ack_events = [row for row in events if row.get("event") == "interrupt_rpc_acknowledged"]
    sent_ns = result.get("interrupt_sent_at_ns", 0)
    ack_ns = result.get("interrupt_ack_at_ns", 0)
    release_ns = release_events[0].get("monotonic_ns", 0) if len(release_events) == 1 else 0
    request_ns = requests[0].get("received_monotonic_ns", 0) if len(requests) == 1 else 0
    checks = {
        "frozen_candidate_hash_matches": sha(PACKAGE / "run_a01.py") ==
            freeze.get("candidate", {}).get("sha256"),
        "installed_cli_identity_matches_freeze": freeze.get("app_server", {}).get("version") == EXPECTED_VERSION and
            freeze.get("app_server", {}).get("sha256") == sha(freeze.get("app_server", {}).get("path", "")) and
            result.get("app_server_version") == EXPECTED_VERSION,
        "one_loopback_responses_request": len(requests) == 1 and
            requests[0].get("path") == "/v1/responses" and
            requests[0].get("peer_ip") == "127.0.0.1" and
            requests[0].get("body_sha256") and
            result.get("mock_listener_ip") == "127.0.0.1" and
            result.get("mock_request_count") == 1,
        "pending_stream_preceded_interrupt": len(request_events) == 1 and
            len(open_events) == 1 and request_ns < open_events[0].get("monotonic_ns", 0) < sent_ns,
        "matching_interrupt_rpc_accepted": result.get("interrupt_rpc_accepted") is True and
            result.get("interrupt_rpc_error") is False and len(ack_events) == 1 and
            ack_events[0].get("accepted") is True and sent_ns <= ack_ns,
        "no_socket_close_observed_during_two_second_window": not close_events and
            result.get("provider_socket_closed_before_release") is False and
            result.get("provider_socket_close_at_ns") is None and
            result.get("pre_release_wait_seconds") == 2.0 and
            release_ns >= ack_ns + 2_000_000_000,
        "interrupted_terminal_arrived_after_interrupt_before_release":
            result.get("matching_turn_completion_observed") is True and
            result.get("completion_thread_matches") is True and
            result.get("completion_turn_matches") is True and
            result.get("turn_completion_status") == "interrupted" and
            sent_ns <= result.get("turn_completion_at_ns", 0) < release_ns,
        "mock_and_app_server_cleanup_valid": result.get("mock_errors") == [] and
            str(process_exit).strip() == "0" and result.get("app_server_exit_code") == 0,
        "scientific_fail_exit_is_consistent": result.get("disposition") == OBSERVED_FAIL and
            str(runner_exit).strip() == "1",
        "user_credential_environment_not_passed": result.get("credentials_passed_to_app_server") is False,
        "unexpected_external_metadata_request_is_disclosed":
            stderr_summary.get("external_featured_plugin_request_attempted") is True and
            stderr_summary.get("external_featured_plugin_response") == "401 Unauthorized" and
            stderr_summary.get("authorization_headers_retained") is False and
            stderr_summary.get("private_stderr_sha256") == result.get("app_server_stderr_sha256"),
    }
    return checks



def self_test():
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    result = {
        "disposition": OBSERVED_FAIL, "app_server_version": EXPECTED_VERSION,
        "mock_requests": [{"path": "/v1/responses", "peer_ip": "127.0.0.1",
            "body_sha256": "a" * 64, "received_monotonic_ns": 10}],
        "mock_request_count": 1, "mock_listener_ip": "127.0.0.1",
        "pending_request_observed": True, "interrupt_sent_at_ns": 20,
        "interrupt_ack_at_ns": 30, "interrupt_rpc_accepted": True,
        "interrupt_rpc_error": False, "provider_socket_closed_before_release": False,
        "provider_socket_close_at_ns": None, "provider_socket_close_kind_before_release": None,
        "pre_release_wait_seconds": 2.0, "turn_completion_at_ns": 25,
        "matching_turn_completion_observed": True, "completion_thread_matches": True,
        "completion_turn_matches": True, "turn_completion_status": "interrupted",
        "credentials_passed_to_app_server": False, "mock_errors": [],
        "app_server_exit_code": 0,
        "mock_events": [
            {"event": "responses_request_received", "monotonic_ns": 11},
            {"event": "mock_response_created_sent", "monotonic_ns": 15},
            {"event": "interrupt_rpc_acknowledged", "monotonic_ns": 31, "accepted": True},
            {"event": "response_release_gate_set", "monotonic_ns": 2_000_000_031}],
    }
    stderr = {"external_featured_plugin_request_attempted": True,
        "external_featured_plugin_response": "401 Unauthorized",
        "authorization_headers_retained": False,
        "private_stderr_sha256": "b" * 64}
    # Match the retained receipt's stderr hash for the positive fixture.
    result["app_server_stderr_sha256"] = stderr["private_stderr_sha256"]
    positive = audit(result, "0", "1", stderr, freeze)
    mutations = {
        "late_socket_close_rejected": lambda r: (
            r.update(provider_socket_closed_before_release=True),
            r.update(provider_socket_close_at_ns=40),
            r.update(provider_socket_close_kind_before_release="eof"),
            r["mock_events"].append({"event": "provider_socket_eof_before_release",
                                     "monotonic_ns": 40})),
        "wrong_peer_rejected": lambda r: r["mock_requests"][0].update(peer_ip="192.0.2.1"),
        "wrong_terminal_rejected": lambda r: r.update(turn_completion_status="completed"),
        "credential_environment_rejected": lambda r: r.update(credentials_passed_to_app_server=True),
    }
    controls = {}
    for name, mutate in mutations.items():
        changed = json.loads(json.dumps(result))
        mutate(changed)
        controls[name] = not all(audit(changed, "0", "1", stderr, freeze).values())
    if not all(positive.values()) or not all(controls.values()):
        raise SystemExit(json.dumps({"positive": positive, "controls": controls}, indent=2))
    print(json.dumps({"positive_checks": len(positive), "mutation_controls": controls,
                      "classification": "valid retained FAIL observation; environment HOLD"}, indent=2))


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_a01_v2.py --self-test | RESULTS_DIR")
    root = Path(sys.argv[1]).resolve()
    result = json.loads((root / "result.json").read_text(encoding="utf-8"))
    stderr_summary = json.loads((root / "app_server_stderr_redacted.json").read_text(encoding="utf-8"))
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    checks = audit(result,
                   (root / "process_exit.txt").read_text(encoding="ascii"),
                   (root / "runner_exit.txt").read_text(encoding="ascii"),
                   stderr_summary, freeze)
    report = {
        "disposition": "AUDIT_VALID_OBSERVED_FAIL_WITH_ENVIRONMENT_HOLD" if all(checks.values()) else "AUDIT_FAILED",
        "scientific_observation": "No TCP EOF/reset was observed in the fixed two-second interval after accepted turn/interrupt; the turn still completed as interrupted before the mock response release.",
        "environment_validity": "HOLD_UNEXPECTED_EXTERNAL_PLUGIN_METADATA_REQUEST",
        "checks": checks,
        "method_note": "App Server stderr records a 401 response from the external featured-plugin endpoint, but request headers were not captured, so auth state is unknown. The provider Responses request itself was served from 127.0.0.1. This prevents a zero-egress claim and may confound one transport run; it is disclosed and no retry was made. No user credential environment variables were passed.",
    }
    (root / "audit_v2.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
