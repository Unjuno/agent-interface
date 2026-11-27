"""Independent saved-raw audit for the A30 one-shot X11 application test."""
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
    manifest = HERE / "SHA256SUMS.txt"
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        actual = sha(HERE / rel)
        results.append({"path": rel, "expected": expected,
                        "actual": actual, "pass": actual == expected})
    return results


def strict_controller_terminal_accepts(release):
    source = (HERE / "map01_overlap_controller_v39.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {"terminal_release_is_known_empty", "require_cover_terminal"}
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in functions} != names:
        raise ValueError("strict terminal helpers missing from frozen controller")
    namespace = {}
    exec(compile(ast.Module(body=functions, type_ignores=[]),
                 "map01_overlap_controller_v39.py", "exec"), namespace)
    terminal = {"event": "terminal", "status": "expired", "release": release}
    try:
        namespace["require_cover_terminal"](terminal)
        return True, terminal
    except (RuntimeError, TypeError, AttributeError) as exc:
        return False, {"terminal": terminal, "error": type(exc).__name__ + ": " + str(exc)}


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
    check("experiment_identity", raw.get("experiment_id") == freeze["experiment_id"],
          raw.get("experiment_id"))
    check("candidate_complete", raw.get("status") == "CANDIDATE_COMPLETE"
          and raw.get("errors") == [], {"status": raw.get("status"),
                                       "errors": raw.get("errors")})

    admission = raw.get("admission")
    check("V4_admission_identity", type(admission) is dict
          and admission.get("event") == "input_admission"
          and admission.get("operation") == "down"
          and admission.get("key") == "a"
          and admission.get("intent_token") == freeze["intent_token"]
          and admission.get("owner_id") == raw.get("owner_id")
          and type(admission.get("input_ack_ns")) is int,
          {"event": admission.get("event") if isinstance(admission, dict) else None,
           "operation": admission.get("operation") if isinstance(admission, dict) else None,
           "key": admission.get("key") if isinstance(admission, dict) else None,
           "owner_id": admission.get("owner_id") if isinstance(admission, dict) else None,
           "intent_token": admission.get("intent_token") if isinstance(admission, dict) else None,
           "input_ack_ns": admission.get("input_ack_ns") if isinstance(admission, dict) else None})

    press = next((row for row in raw.get("key_events", []) if row.get("type") == 2), None)
    release = raw.get("release_event")
    keycode = raw.get("keycode")
    window = raw.get("target_app", {}).get("window_id")
    check("application_received_matching_keypress", type(press) is dict
          and press.get("type") == 2 and press.get("keycode") == keycode
          and press.get("window_id") == window, press)
    check("application_received_matching_keyrelease", type(release) is dict
          and release.get("type") == 3 and release.get("keycode") == keycode
          and release.get("window_id") == window, release)

    effect = raw.get("task_effect", {})
    initial = effect.get("initial_counter")
    after_press = effect.get("after_keypress")
    after_release = effect.get("after_release")
    latency = (effect.get("server_observed_ns", 0) - admission.get("input_ack_ns", 0)
               if isinstance(admission, dict) else None)
    check("application_task_effect", initial == 0 and after_press == 1
          and after_release == 1, {"initial": initial, "after_press": after_press,
                                  "after_release": after_release})
    check("bounded_application_feedback", type(latency) is int and 0 <= latency
          <= freeze["app_response_bound_ns"],
          {"response_latency_ns": latency,
           "bound_ns": freeze["app_response_bound_ns"]})

    deadline = raw.get("lease", {}).get("deadline_ns")
    release_overshoot = (release.get("observed_ns", 0) - deadline
                         if type(release) is dict and type(deadline) is int else None)
    keymap = raw.get("server_keymap", {})
    check("server_keymap_reports_up", keymap.get("key_up") is True
          and type(keymap.get("sampled_ns")) is int,
          keymap)
    check("application_release_after_deadline_within_bound",
          type(release_overshoot) is int and 0 <= release_overshoot
          <= freeze["recovery_bound_ns"],
          {"release_overshoot_ns": release_overshoot,
           "bound_ns": freeze["recovery_bound_ns"]})

    terminal = raw.get("expiry_release")
    supplied_terminal = raw.get("expiry_terminal")
    exact_empty, accepted_terminal = (
        strict_controller_terminal_accepts(terminal)
        if type(terminal) is dict else (False, None))
    terminal_envelope_matches = supplied_terminal == accepted_terminal
    verified_overshoot = raw.get("expiry_verified_overshoot_ns")
    check("current_V39_strict_terminal_release_accepts_receipt",
          exact_empty and terminal_envelope_matches,
          {"saved_terminal": supplied_terminal,
           "replayed_terminal": accepted_terminal,
           "saved_matches_replay": terminal_envelope_matches})
    check("owner_expiry_recovery_is_bounded", type(terminal) is dict
          and terminal.get("reason") == "expired"
          and type(verified_overshoot) is int and 0 <= verified_overshoot
          <= freeze["recovery_bound_ns"],
          {"reason": terminal.get("reason") if isinstance(terminal, dict) else None,
           "verified_overshoot_ns": verified_overshoot,
           "bound_ns": freeze["recovery_bound_ns"]})

    cleanup = raw.get("cleanup", {})
    check("owner_stopped_and_closed", cleanup.get("owner_closed") is True
          and cleanup.get("owner_stopped") is True
          and cleanup.get("owner_thread_alive") is False
          and cleanup.get("owner_error") is None
          and cleanup.get("owner_close_error") is None, cleanup)
    check("xvfb_exited_cleanly", cleanup.get("xvfb_exit") == 0, cleanup)

    passed = all(row["pass"] for row in checks)
    status = ("PASS" if passed else
              ("FAIL" if raw.get("input_dispatch_attempted") else "HOLD"))
    result = {
        "schema": "map01-v39-wslc-xvfb-app-effect-audit-a30-v1",
        "experiment_id": freeze["experiment_id"],
        "status": status,
        "independent_audit": True,
        "source": "saved RAW.json plus frozen input bytes; did not import candidate.py",
        "checks": checks,
        "scope": freeze["scope"],
        "interpretation": (
            "A synthetic X11 application consumed one V4-owner keypress, changed its "
            "server-visible task counter, then received the bounded lease-expiry release. "
            "This does not establish Doom/MAP01 behavior, physical input, a live model, "
            "or general response latency."
        ),
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(checks),
                      "failed": [row["name"] for row in checks if not row["pass"]]},
                     sort_keys=True))
    return 0 if passed else (4 if status == "HOLD" else 3)


if __name__ == "__main__":
    raise SystemExit(main())