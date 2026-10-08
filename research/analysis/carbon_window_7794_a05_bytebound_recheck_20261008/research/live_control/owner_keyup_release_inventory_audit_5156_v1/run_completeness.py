"""One synthetic fake-Xlib execution plus expected-inventory mutation controls."""
import copy
import io
import json
import sys
import types
import uuid
import unittest

from audit_expected_release_inventory import audit as candidate_audit
from audit_owner_release_brackets import audit as baseline_audit
from test_owner_integration import OwnerIntegrationTests, FakeLease


def joined_rows(trace, expected):
    rows = [r for r in trace["owner_records"] if r.get("event") == "owner_key_release_bracket"]
    output = []
    for row, release in zip(rows, expected["releases"]):
        caller = trace["caller_receipts"][release["caller_index"]]
        output.append(dict(row, caller_started_ns=caller["started_ns"],
                          caller_returned_ns=caller["returned_ns"]))
    return output


def mutation_results(trace, expected):
    results = {}
    empty = {"admissions": [], "caller_receipts": [], "owner_records": []}
    results["empty_trace"] = candidate_audit(empty, expected)
    omitted = copy.deepcopy(trace)
    omitted["owner_records"] = [r for r in omitted["owner_records"]
                                if r.get("event") != "owner_key_release_bracket"]
    results["all_brackets_omitted"] = candidate_audit(omitted, expected)
    one_missing = copy.deepcopy(trace)
    removed = False
    filtered = []
    for row in one_missing["owner_records"]:
        if not removed and row.get("event") == "owner_key_release_bracket":
            removed = True
            continue
        filtered.append(row)
    one_missing["owner_records"] = filtered
    results["one_bracket_deleted"] = candidate_audit(one_missing, expected)
    no_admission = copy.deepcopy(trace)
    no_admission["admissions"].pop(0)
    results["one_admission_deleted"] = candidate_audit(no_admission, expected)
    no_terminal = copy.deepcopy(trace)
    no_terminal["owner_records"] = [r for r in no_terminal["owner_records"]
                                    if not (r.get("event") == "owner_release"
                                            and r.get("reason") == "release")]
    results["terminal_deleted"] = candidate_audit(no_terminal, expected)
    tampered = copy.deepcopy(trace)
    next(r for r in tampered["owner_records"]
         if r.get("event") == "owner_key_release_bracket")["keycode"] = 999
    results["keycode_tampered"] = candidate_audit(tampered, expected)
    bad_clock = copy.deepcopy(trace)
    first = next(r for r in bad_clock["owner_records"]
                 if r.get("event") == "owner_key_release_bracket")
    first["request_returned_ns"] = first["request_started_ns"] - 1
    results["timestamp_inverted"] = candidate_audit(bad_clock, expected)
    return results


def run(expected):
    executor = types.ModuleType("executor_v3")
    class Cancelled(Exception):
        pass
    class DecisionRequired(Exception):
        pass
    executor.Cancelled, executor.DecisionRequired = Cancelled, DecisionRequired
    sys.modules["executor_v3"] = executor
    test_output = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OwnerIntegrationTests)
    test_result = unittest.TextTestRunner(stream=test_output, verbosity=2).run(suite)
    fixtures = OwnerIntegrationTests()
    fixed_uuid = types.SimpleNamespace(hex=expected["owner_id"])
    original_uuid4 = uuid.uuid4
    try:
        uuid.uuid4 = lambda: fixed_uuid
        owner = fixtures.transition_v3.InputOwner("fake-display",
                                                  _owner_cls=fixtures.v11.InputOwner)
        display = fixtures.displays[-1]
        owner_id = owner.owner_id
        explicit = FakeLease()
        explicit.intent_token = "intent-explicit"
        cleanup = FakeLease()
        cleanup.intent_token = "intent-cleanup"

        admissions = []
        def down(lease, key, code):
            result = owner.call("down", lease, key)
            admissions.append({"owner_id": owner_id, "intent_token": lease.intent_token,
                               "key": key, "keycode": code, "receipt": result})

        callers = []
        def release_call(operation, lease, key=None):
            result = owner.call(operation, lease, key)
            callers.append({
                "operation": operation, "owner_id": owner_id,
                "intent_token": lease.intent_token, "key": key,
                "started_ns": result["release_call_started_ns"],
                "returned_ns": result["release_call_returned_ns"],
                "receipt": result,
            })

        try:
            down(explicit, "a", 38)
            release_call("up", explicit, "a")
            release_call("release", explicit)
            down(cleanup, "b", 56)
            down(cleanup, "a", 38)
            release_call("release", cleanup)
        finally:
            owner.close()
        trace = {"admissions": admissions, "caller_receipts": callers,
                 "owner_records": owner.records}
        baseline_rows = joined_rows(trace, expected)
        candidate_errors = candidate_audit(trace, expected)
        controls = mutation_results(trace, expected)
        baseline_controls = {
            "pristine": baseline_audit(baseline_rows),
            "empty": baseline_audit([]),
            "all_brackets_omitted": baseline_audit([
                r for r in owner.records if r.get("event") != "owner_key_release_bracket"
            ]),
            "one_bracket_deleted": baseline_audit(baseline_rows[1:]),
        }
        v10 = fixtures.transition_v3.InputOwner("fake-display",
                                                 _owner_cls=fixtures.v10.InputOwner)
        v10_display = fixtures.displays[-1]
        v10_lease1, v10_lease2 = FakeLease(), FakeLease()
        v10_lease1.intent_token, v10_lease2.intent_token = "intent-explicit", "intent-cleanup"
        v10.call("down", v10_lease1, "a")
        v10.call("up", v10_lease1, "a")
        v10.call("release", v10_lease1)
        v10.call("down", v10_lease2, "b")
        v10.call("down", v10_lease2, "a")
        v10.call("release", v10_lease2)
        v10.close()
        terminal_rows = [r for r in owner.records if r.get("event") == "owner_release"]
        expected_request_sequence = [(2,38),(3,38),(2,56),(2,38),(3,56),(3,38)]
        v10_v11_equivalent = (
            v10_display.events == display.events
            and v10_display.sync_count == display.sync_count
            and v10_display.keys_down == display.keys_down == set()
            and [(e[0],e[1]) for e in display.events] == expected_request_sequence
        )
        baseline_fail_open = all(not baseline_controls[k] for k in
                                 ("pristine","empty","all_brackets_omitted","one_bracket_deleted"))
        mutations_rejected = all(bool(errors) for errors in controls.values())
        return {
            "status": "PASS_RELEASE_INVENTORY_AUDIT_CONSTRUCTION" if (
                not candidate_errors and len(terminal_rows) == len(expected["terminals"])
                and test_result.wasSuccessful() and test_result.testsRun == 14
                and v10_v11_equivalent and baseline_fail_open and mutations_rejected
            ) else "FAIL_RELEASE_INVENTORY_AUDIT_CONSTRUCTION",
            "runtime": {"python": sys.version.split()[0],
                        "platform": sys.platform,
                        "execution": "host fake-Xlib; no real display or input"},
            "existing_owner_suite": {"tests_run": test_result.testsRun,
                                     "failures": len(test_result.failures),
                                     "errors": len(test_result.errors),
                                     "stdout": test_output.getvalue()},
            "baseline_auditor": baseline_controls,
            "candidate_pristine_errors": candidate_errors,
            "candidate_mutation_results": controls,
            "owner_behavior": {
                "expected_request_sequence": expected_request_sequence,
                "v10_requests": v10_display.events,
                "v11_requests": display.events,
                "v10_sync_count": v10_display.sync_count,
                "v11_sync_count": display.sync_count,
                "v10_final_keys_down": sorted(v10_display.keys_down),
                "v11_final_keys_down": sorted(display.keys_down),
                "terminal_count": len(terminal_rows),
                "all_terminals_verified_neutral": all(r.get("verified") is True
                    and r.get("keys_down") == [] and r.get("buttons_down") == []
                    for r in terminal_rows),
                "v10_v11_behavior_equivalent": v10_v11_equivalent,
            },
            "trace": trace,
        }
    finally:
        uuid.uuid4 = original_uuid4


if __name__ == "__main__":
    inventory = json.loads(sys.argv[1])
    print(json.dumps(run(inventory), sort_keys=True, separators=(",", ":")))
