"""Independent saved-row check for the V13/V4 release-batch bridge probe."""
import json
import sys
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit("FAIL: " + message)


def main(path):
    row = json.loads(Path(path).read_text(encoding="utf-8"))
    rpc = row.get("v13_release_rpc_receipt")
    keyup = row.get("owner_thread_keyup_receipt")
    require(type(rpc) is dict and type(keyup) is dict,
            "nested V13 RPC or owner key-up receipt is absent")
    require(row.get("event") == "input_release_transition", "transition event absent")
    require(row.get("transition_schema") == "input-release-transition-v3",
            "V4 transition schema mismatch")
    require(row.get("release_batch_schema") == "input-release-batch-v3",
            "release batch schema mismatch")
    require(row.get("release_batch_complete") is True
            and row.get("release_batch_size") == 1
            and row.get("release_batch_position") == 0,
            "one-row release batch is not complete")
    require(row.get("owner_id") == rpc.get("owner_id") == keyup.get("owner_id"),
            "owner identity does not join")
    require(row.get("intent_token") == rpc.get("intent_token") == keyup.get("intent_token"),
            "intent token does not join")
    require(row.get("operation") == rpc.get("operation") == keyup.get("operation") == "up"
            and row.get("key") == rpc.get("payload") == keyup.get("key"),
            "release operation/key does not join")
    require(row.get("valid_until_ns") == rpc.get("valid_until_ns")
            == keyup.get("valid_until_ns"), "lease deadline does not join")
    call_start = row.get("release_call_started_ns")
    call_end = row.get("release_call_returned_ns")
    rpc_start = rpc.get("call_started_ns")
    rpc_end = rpc.get("call_returned_ns")
    keyup_start = keyup.get("owner_keyrelease_started_ns")
    keyup_end = keyup.get("owner_sync_returned_ns")
    require(all(type(value) is int for value in
                (call_start, call_end, rpc_start, rpc_end, keyup_start, keyup_end)),
            "release time bounds are not integer nanoseconds")
    require(call_start <= rpc_start <= rpc_end <= call_end,
            "V13 RPC interval escaped V4 caller interval")
    require(call_start <= keyup_start <= keyup_end <= call_end,
            "owner KeyRelease/XSync interval escaped caller interval")
    require(rpc.get("release_transition_interval_ns") == [rpc_start, rpc_end],
            "V13 interval does not match its endpoints")
    require(row.get("v13_release_rpc_receipt_valid") is True
            and row.get("owner_thread_keyup_verified") is True
            and row.get("ordinary_release_candidate") is True,
            "release receipts did not pass bridge validation")
    require(row.get("owner_transition_verified") is True
            and row.get("owner_thread_keyup_verified") is True
            and row.get("owner_thread_keyup_verified_after_batch") is True
            and row.get("owner_sample_ordered_after_batch") is True,
            "batch consumer did not verify the joined receipts")
    require(row.get("owned_keycodes_after_batch") == [],
            "owner sample was not empty after batch")
    sample_start = row.get("owner_sample_after_started_ns")
    sample_end = row.get("owner_sample_after_finished_ns")
    require(type(sample_start) is int and type(sample_end) is int
            and call_end <= sample_start <= sample_end,
            "after-batch owner sample is not ordered after release")
    require(rpc.get("x11_release_and_sync_completed_before_return") is True
            and keyup.get("server_sync_completed") is True,
            "synchronous release receipts are absent")
    require(rpc.get("continuous_physical_state_sampled") is False
            and rpc.get("application_consumption_observed") is False
            and rpc.get("grants_input_authority") is False
            and row.get("grants_input_authority") is False
            and keyup.get("physical_verification_authoritative") is False
            and row.get("physical_verification_authoritative") is False,
            "construction row overclaims physical/application authority")
    print("PASS_SAVED_ROW_V13_V4_RELEASE_BATCH_BRIDGE")
    print("checks=18; authority_granted=false; physical_or_application_effect=unobserved")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_v13_v4_backend_bridge.py TRACE.json")
    main(sys.argv[1])
