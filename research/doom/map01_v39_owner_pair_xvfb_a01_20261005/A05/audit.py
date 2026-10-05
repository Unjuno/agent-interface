"""Independent structural/outcome audit of candidate.py's immutable raw."""
import json
import sys
from pathlib import Path


def fail(message):
    raise ValueError(message)


def audit(path):
    raw = json.loads(Path(path).read_text())
    if raw.get("schema") != "v39-owner-pair-xvfb-a05-raw-v1":
        fail("wrong raw schema")
    keycode = raw.get("keycode")
    if type(keycode) is not int or not 8 <= keycode <= 255:
        fail("invalid keycode")
    for field, expected in (("control_samples", [False, True, False]),
                            ("pair_samples", [False, True, True, False, False])):
        samples = raw.get(field)
        if type(samples) is not list or [s.get("key_down") for s in samples] != expected:
            fail(field + " state sequence mismatch")
        for sample in samples:
            if len(bytes.fromhex(sample["bitmap_hex"])) != 32:
                fail(field + " malformed keymap")
            if sample.get("keycode") != keycode:
                fail(field + " keycode mismatch")
            if type(sample.get("started_ns")) is not int or type(sample.get("finished_ns")) is not int or sample["started_ns"] > sample["finished_ns"]:
                fail(field + " sample interval invalid")
    control_up = raw.get("control_up_receipt")
    if type(control_up) is not list or len(control_up) != 1 or type(control_up[0]) is not dict:
        fail("control up_batch did not return exactly one receipt")
    if control_up[0].get("owner_thread_keyup_verified") is not True:
        fail("control key-up not reported verified")
    if raw.get("control_state_after_up", {}).get("owned_keycodes") != []:
        fail("control owner retained a key after up_batch")
    if raw.get("owner_ids", {}).get("A") == raw.get("owner_ids", {}).get("B"):
        fail("owners are not distinct")
    if raw.get("intent_tokens", {}).get("A") == raw.get("intent_tokens", {}).get("B"):
        fail("leases are not distinct")
    a_up = raw.get("A_up_receipt")
    if type(a_up) is not list or len(a_up) != 1 or type(a_up[0]) is not dict:
        fail("A up_batch did not return exactly one receipt")
    if a_up[0].get("owner_thread_keyup_verified") is not True:
        fail("A key-up not reported verified")
    if raw.get("B_state_after_A_up", {}).get("owned_keycodes") != [keycode]:
        fail("B local bookkeeping did not retain W after A's up")
    b_up = raw.get("B_up_receipt")
    if type(b_up) is not list or len(b_up) != 1 or type(b_up[0]) is not dict:
        fail("B up_batch did not return exactly one receipt")
    if b_up[0].get("owner_thread_keyup_verified") is not True:
        fail("B key-up not reported verified")
    if raw.get("B_state_after_B_up", {}).get("owned_keycodes") != []:
        fail("B local bookkeeping not empty after its up")
    if raw.get("final_sample", {}).get("key_down") is not False:
        fail("final server keymap not neutral")
    if raw.get("cleanup_errors") != []:
        fail("cleanup errors recorded")
    for identity in ("A", "B"):
        receipts = [r for r in raw["owner_records"][identity]
                    if isinstance(r, dict) and r.get("event") == "owner_explicit_keyup"]
        if len(receipts) != 1 or receipts[0].get("server_keyup_verified") is not True:
            fail(identity + " owner history does not contain one verified explicit up")
        attempts = receipts[0].get("server_keyup_attempts")
        if type(attempts) is not list or not attempts or attempts[-1].get("server_key_down_after") is not False:
            fail(identity + " explicit-up attempt history invalid")
    return {
        "status": "CONFIRMED_SHARED_DISPLAY_CROSS_OWNER_RELEASE",
        "control_server_keymap": [False, True, False],
        "pair_server_keymap": [False, True, True, False, False],
        "A_receipt_verified_after_global_up": True,
        "B_local_hold_persisted_after_A_release": True,
        "B_receipt_verified_after_global_up": True,
        "scope": "one private Xvfb server and two current candidate owner instances only",
        "error_count": 0,
    }


if __name__ == "__main__":
    try:
        result = audit(sys.argv[1])
    except Exception as exc:
        print(json.dumps({"status": "FAIL_AUDIT", "error": repr(exc)}, sort_keys=True))
        raise SystemExit(1)
    print(json.dumps(result, sort_keys=True))
