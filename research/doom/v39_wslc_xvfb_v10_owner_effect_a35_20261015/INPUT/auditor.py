"""Independent raw-only audit for A35; does not import the candidate."""
import argparse
import ast
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checksummed_inputs():
    results = []
    for line in (HERE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        actual = sha(HERE / rel)
        results.append({"path": rel, "expected": expected,
                        "actual": actual, "pass": actual == expected})
    return results


def strict_predicates():
    source = (HERE / "map01_overlap_controller_v39.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {"terminal_release_is_known_empty", "require_cover_terminal"}
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in functions} != names:
        raise ValueError("current V39 release predicates are absent")
    namespace = {}
    exec(compile(ast.Module(body=functions, type_ignores=[]),
                 "map01_overlap_controller_v39.py", "exec"), namespace)
    return namespace


def cleanup_empty_release_predicate():
    source = (HERE / "doom_controller_failure_cleanup_v1.py").read_text(
        encoding="utf-8")
    tree = ast.parse(source)
    functions = [node for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef)
                 and node.name == "empty_release"]
    if len(functions) != 1:
        raise ValueError("merged #8771 empty-release predicate is absent or ambiguous")
    namespace = {}
    exec(compile(ast.Module(body=functions, type_ignores=[]),
                 "doom_controller_failure_cleanup_v1.py", "exec"), namespace)
    return namespace["empty_release"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    checks = []

    def check(name, passed, observed):
        checks.append({"name": name, "pass": bool(passed), "observed": observed})

    manifest = checksummed_inputs()
    check("frozen_input_manifest", all(row["pass"] for row in manifest), manifest)
    source_matches = {
        name: sha(HERE / name) == expected
        for name, expected in freeze["source_sha256"].items()}
    check("merged_main_source_identity", all(source_matches.values()), source_matches)
    check("experiment_identity", raw.get("experiment_id") == freeze["experiment_id"],
          raw.get("experiment_id"))
    check("candidate_complete", raw.get("status") == "CANDIDATE_COMPLETE"
          and raw.get("errors") == [] and raw.get("candidate_complete") is True,
          {"status": raw.get("status"), "errors": raw.get("errors"),
           "candidate_complete": raw.get("candidate_complete")})

    dispatch = raw.get("dispatch", {})
    admission = raw.get("admission", {})
    deadline = raw.get("lease", {}).get("deadline_ns")
    ack = admission.get("input_ack_ns")
    check("V10_admission_matches_dispatch", type(admission) is dict
          and admission.get("event") == "input_admission"
          and admission.get("key") == dispatch.get("key") == "a"
          and dispatch.get("operation") == "down"
          and dispatch.get("intent") == freeze["intent_token"]
          and dispatch.get("deadline_ns") == deadline
          and admission.get("valid_until_ns") == deadline
          and type(ack) is int and type(dispatch.get("started_ns")) is int
          and dispatch["started_ns"] <= ack < deadline,
          {"dispatch": dispatch, "admission": admission})

    messages = raw.get("app_messages", [])
    press = next((row for row in messages
                  if type(row) is dict and row.get("event") == "app_keypress_effect"), None)
    release_event = raw.get("app_release")
    stopped = next((row for row in messages
                    if type(row) is dict and row.get("event") == "app_stopped"), None)
    press_count = sum(type(row) is dict and row.get("event") == "app_keypress_effect"
                      for row in messages)
    release_count = sum(type(row) is dict and row.get("event") == "app_keyrelease"
                        for row in messages)
    task = raw.get("task_effect", {})
    keycode = dispatch.get("keycode")
    window = raw.get("app", {}).get("window_id")
    check("separate_app_received_matching_keypress", type(press) is dict
          and press.get("type") == 2 and press.get("keycode") == keycode
          and press.get("window_id") == window,
          press)
    check("exactly_one_matching_press_and_release", press_count == 1
          and release_count == 1,
          {"keypress_effect_count": press_count,
           "keyrelease_count": release_count})
    check("app_task_effect_observed_independently", task.get("initial_counter") == 0
          and task.get("after_keypress") == 1
          and task.get("independent_counter_after_keypress") == 1
          and task.get("after_release") == 1,
          {"task_effect": task, "app_report": press})
    response_ns = task.get("response_latency_ns")
    check("bounded_application_feedback", type(response_ns) is int
          and 0 <= response_ns <= freeze["app_response_bound_ns"],
          {"response_latency_ns": response_ns,
           "bound_ns": freeze["app_response_bound_ns"]})
    check("separate_app_received_matching_keyrelease", type(release_event) is dict
          and release_event.get("type") == 3
          and release_event.get("keycode") == keycode
          and release_event.get("window_id") == window,
          release_event)
    check("app_terminal_task_state_preserved", type(stopped) is dict
          and stopped.get("counter") == 1,
          stopped)

    release = raw.get("expiry_release")
    overshoot = raw.get("owner_expiry_overshoot_ns")
    check("V10_release_is_verified_known_empty", type(release) is dict
          and release.get("event") == "owner_release"
          and release.get("reason") == "expired"
          and release.get("verified") is True
          and release.get("keys_down") == []
          and release.get("buttons_down") == []
          and release.get("keys_unknown") == []
          and release.get("key_state_errors") == [], release)
    check("bounded_expiry_recovery", type(overshoot) is int
          and 0 <= overshoot <= freeze["recovery_bound_ns"],
          {"overshoot_ns": overshoot,
           "bound_ns": freeze["recovery_bound_ns"]})
    release_ns = release_event.get("release_ns") if type(release_event) is dict else None
    check("app_release_arrived_within_recovery_bound", type(release_ns) is int
          and type(deadline) is int and deadline <= release_ns
          <= deadline + freeze["recovery_bound_ns"],
          {"release_ns": release_ns, "deadline_ns": deadline,
           "bound_ns": freeze["recovery_bound_ns"]})
    server = raw.get("server_keymap", {})
    check("independent_X11_keymap_reports_up", server.get("key_up") is True
          and server.get("keycode") == keycode
          and server.get("source") == "independent X11 connection query_keymap",
          server)

    terminal = raw.get("terminal")
    predicates = strict_predicates()
    try:
        predicates["require_cover_terminal"](terminal)
        strict_accept = True
        strict_error = None
    except (RuntimeError, TypeError, AttributeError) as exc:
        strict_accept = False
        strict_error = type(exc).__name__ + ": " + str(exc)
    check("current_V39_predicate_accepts_V10_expiry_receipt", strict_accept,
          {"terminal": terminal, "error": strict_error})
    cleanup_accepts = cleanup_empty_release_predicate()(release)
    check("merged_PR8771_predicate_accepts_V10_release", cleanup_accepts, release)
    mutation_results = {}
    if type(release) is dict:
        cleanup_predicate = cleanup_empty_release_predicate()
        for field in ("keys_unknown", "key_state_errors"):
            mutated = dict(release)
            mutated.pop(field, None)
            mutation_terminal = dict(terminal, release=mutated)
            try:
                predicates["require_cover_terminal"](mutation_terminal)
                v39_rejected = False
            except (RuntimeError, TypeError, AttributeError):
                v39_rejected = True
            mutation_results[field] = {
                "v39_rejected": v39_rejected,
                "cleanup_rejected": cleanup_predicate(mutated) is False,
            }
    check("missing_known_empty_fields_are_rejected_by_both_predicates",
          mutation_results == {
              "keys_unknown": {"v39_rejected": True, "cleanup_rejected": True},
              "key_state_errors": {"v39_rejected": True, "cleanup_rejected": True}},
          mutation_results)

    cleanup = raw.get("cleanup", {})
    owner_rows = raw.get("owner_records", [])
    check("expiry_receipt_is_from_V10_owner_history",
          type(release) is dict and release in owner_rows,
          {"release": release, "owner_record_count": len(owner_rows)})
    check("owner_and_app_stopped_cleanly", cleanup.get("owner_closed") is True
          and cleanup.get("owner_stopped") is True
          and cleanup.get("owner_thread_alive") is False
          and cleanup.get("owner_error") is None
          and cleanup.get("app_exit") == 0
          and cleanup.get("xvfb_exit") == 0,
          cleanup)

    passed = sum(row["pass"] for row in checks)
    result = {"schema": "map01-v39-wslc-v10-owner-effect-audit-a35-v1",
              "experiment_id": freeze["experiment_id"],
              "scope": freeze["scope"], "checks": checks,
              "independent_audit": True,
              "status": "PASS" if passed == len(checks) else "FAIL",
              "passed": passed, "total": len(checks)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"status": result["status"], "passed": passed,
                      "total": len(checks)}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
