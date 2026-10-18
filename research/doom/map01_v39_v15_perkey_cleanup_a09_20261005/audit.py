#!/usr/bin/env python3
"""Independent exact-shape audit of the retained A09 fake-X candidate raw."""
import json
import pathlib
import sys


EXPECTED_RUN = "a09-current-main-712a71b-20261005-one-shot"


def audit(path):
    raw = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    failures = []
    if raw.get("schema") != "v39-v15-keyup-loss-a09-raw-v1":
        failures.append("wrong raw schema")
    if raw.get("run_id") != EXPECTED_RUN:
        failures.append("wrong run identity")
    if raw.get("source_base") != "712a71b25dc024b5406b24b568225c0663e7278b":
        failures.append("wrong source base")
    if raw.get("claims") != {
            "real_x11": False, "gui": False, "doom": False, "model": False,
            "physical_keyboard": False, "application_effect": False}:
        failures.append("scope claims are not all explicitly false")
    cases = raw.get("cases")
    if type(cases) is not list or len(cases) != 2:
        failures.append("expected exactly two fixed arms")
        cases = []
    by_arm = {case.get("injected_keyrelease_loss"): case
              for case in cases if type(case) is dict}
    if set(by_arm) != {False, True} or len(by_arm) != 2:
        failures.append("arms are missing or duplicated")

    def require(condition, message):
        if not condition:
            failures.append(message)

    for drop in (False, True):
        case = by_arm.get(drop)
        if case is None:
            continue
        label = "treatment" if drop else "control"
        require(case.get("dropped_keyrelease_count") == int(drop),
                f"{label}: injected KeyRelease drop count differs")
        terminal = case.get("executor_terminal")
        require(type(terminal) is dict, f"{label}: terminal missing")
        if type(terminal) is dict:
            require(terminal.get("status") == "completed",
                    f"{label}: terminal not completed")
            require(terminal.get("steps_completed") == 1,
                    f"{label}: expected exactly one completed step")
            release = terminal.get("release")
            require(type(release) is dict and release.get("verified") is True,
                    f"{label}: terminal release is not verified")
        require(case.get("server_keycodes_down_after_executor_release") == [],
                f"{label}: fake server retained a key after executor release")
        require(case.get("owner_close_recovered") is True,
                f"{label}: owner close did not observe empty fake keymap")
        row = case.get("release_row")
        require(type(row) is dict, f"{label}: explicit release transition missing")
        if type(row) is not dict:
            continue
        receipt = row.get("owner_thread_keyup_receipt")
        require(type(receipt) is dict,
                f"{label}: owner-thread key-up receipt missing")
        if type(receipt) is not dict:
            continue
        attempts = receipt.get("server_keyup_attempts")
        expected_count = 2 if drop else 1
        require(type(attempts) is list and len(attempts) == expected_count,
                f"{label}: expected {expected_count} owner attempt(s)")
        if type(attempts) is list and len(attempts) == expected_count:
            require(receipt.get("server_keyup_attempt_count") == expected_count,
                    f"{label}: reported attempt count differs")
            first = attempts[0]
            require(first.get("server_key_down_before") is True,
                    f"{label}: first attempt did not start with key down")
            if drop:
                require(first.get("server_key_down_after") is True,
                        "treatment: first dropped release was not observed still down")
                second = attempts[1]
                require(second.get("server_key_down_before") is True,
                        "treatment: retry did not begin with key still down")
                require(second.get("server_key_down_after") is False,
                        "treatment: retry did not clear fake server key state")
            else:
                require(first.get("server_key_down_after") is False,
                        "control: normal key-up did not clear fake server key state")

    return {"schema": "v39-v15-keyup-loss-a09-audit-v1",
            "run_id": EXPECTED_RUN,
            "candidate_cases": len(cases),
            "failures": failures,
            "pass": not failures,
            "classification": "PASS_CONSTRUCTION_SCOPED" if not failures
                               else "FAIL_OR_INCOMPLETE_CONSTRUCTION"}


if __name__ == "__main__":
    result = audit(sys.argv[1])
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)
