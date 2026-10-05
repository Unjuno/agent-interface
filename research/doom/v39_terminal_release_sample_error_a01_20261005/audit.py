"""Independent raw-only audit for V39 cleanup keymap-sampling failure."""
import copy
import json
import sys
from pathlib import Path


def valid(raw):
    if type(raw) is not dict or raw.get("schema") != "v39-terminal-release-sample-error-raw-v1":
        return False
    if raw.get("test") != "test_terminal_cleanup_sample_failure_retains_unverified_receipt_and_retries":
        return False
    keycode = raw.get("keycode")
    events = raw.get("key_events")
    trace = raw.get("trace")
    failed = raw.get("failed_release_receipt")
    recovered = raw.get("recovery_release_receipt")
    if type(keycode) is not int or type(events) is not list or type(trace) is not list:
        return False
    if type(failed) is not dict or type(recovered) is not dict:
        return False
    if raw.get("keymap_query_attempts") != 2:
        return False
    # Xlib KeyPress/KeyRelease are 2/3 in the frozen fake server.
    if events != [[2, keycode], [3, keycode], [3, keycode]]:
        return False
    timeline = [(row[0], row[1:]) for row in trace if type(row) is list and row]
    first_up = next((i for i, (kind, rest) in enumerate(timeline)
                     if kind == "key_event" and rest == [3, keycode]), None)
    failure_sample = next((i for i, (kind, rest) in enumerate(timeline)
                           if kind == "query_keymap" and rest[:1] == ["raise"]), None)
    second_up = next((i for i, (kind, rest) in enumerate(timeline)
                      if kind == "key_event" and rest == [3, keycode]
                      and first_up is not None and i > first_up), None)
    success_sample = next((i for i, (kind, rest) in enumerate(timeline)
                           if kind == "query_keymap" and rest[:1] == ["return"]), None)
    if None in (first_up, failure_sample, second_up, success_sample):
        return False
    if not (first_up < failure_sample < second_up < success_sample):
        return False
    if failed.get("event") != "owner_release" or failed.get("verified") is not False:
        return False
    if failed.get("keys_down") != [] or failed.get("keys_unknown") != [keycode]:
        return False
    errors = failed.get("key_state_errors")
    if (type(errors) is not list or len(errors) != 1
            or errors[0].get("source") != "keymap"
            or errors[0].get("type") != "RuntimeError"):
        return False
    if recovered.get("event") != "owner_release" or recovered.get("verified") is not True:
        return False
    if recovered.get("keys_down") != [] or recovered.get("keys_unknown") != []:
        return False
    if raw.get("server_keys_after_failed_sample") != []:
        return False
    if raw.get("server_keys_after_recovery") != []:
        return False
    raised = raw.get("raised_error")
    if (type(raised) is not dict or raised.get("type") != "RuntimeError"
            or raised.get("has_owner_release_record") is not True):
        return False
    return True


def main(output_dir):
    root = Path(output_dir)
    raw = json.loads((root / "cleanup-sample-failure.raw.json").read_text(encoding="utf-8"))
    candidate = json.loads((root / "candidate.result.json").read_text(encoding="utf-8"))
    stdout = (root / "candidate.stdout").read_text(encoding="utf-8")
    candidate_ok = (candidate.get("successful") is True and candidate.get("exit_code") == 0
                    and candidate.get("tests_run") == 1 and "OK" in stdout)

    mutations = {}
    for name, change in {
        "remove_first_keyrelease": lambda value: value.update(
            key_events=[[2, value["keycode"]], [3, value["keycode"]]]),
        "claim_failed_sample_verified": lambda value: value["failed_release_receipt"].update(verified=True),
        "omit_unknown_key": lambda value: value["failed_release_receipt"].update(keys_unknown=[]),
        "omit_sample_error": lambda value: value["failed_release_receipt"].update(key_state_errors=[]),
        "move_error_before_up": lambda value: value.update(trace=[
            ["query_keymap", "raise", []], ["key_event", 3, value["keycode"]]]),
        "fail_recovery_verification": lambda value: value["recovery_release_receipt"].update(verified=False),
    }.items():
        mutated = copy.deepcopy(raw)
        change(mutated)
        mutations[name] = valid(mutated) is False

    result = {
        "schema": "v39-terminal-release-sample-error-audit-v1",
        "status": ("PASS_SYNTHETIC_CLEANUP_SAMPLE_FAILURE"
                   if candidate_ok and valid(raw) and all(mutations.values()) else "FAIL_AUDIT"),
        "candidate_stdout_ok": candidate_ok,
        "raw_baseline_valid": valid(raw),
        "mutation_controls_rejected": mutations,
        "mutation_controls_rejected_count": sum(mutations.values()),
        "mutation_controls_total": len(mutations),
        "scope": "Fake X server and selected V12/V3/V4 owner path only; no real X server, physical input, GUI, application effect, live model/game, or allocation.",
    }
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    (root / "audit.json").write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py OUTPUT_DIR")
    raise SystemExit(main(sys.argv[1]))
