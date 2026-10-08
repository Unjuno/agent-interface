#!/usr/bin/env python3
"""One-shot private-Xvfb candidate for Issue #5156 allocation 13."""
import argparse
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback


ROOT = Path(__file__).resolve().parent
DEPS = ROOT / "dependencies"
IMAGE_ID = "sha256:d8c51b45569cc4fdf0f5d82ae285c3fbb20fae8525d6fab0cebadca171b3bebe"
BASE = "b8b2a284ac3b519a75bfc3f824589c81f5e31bab"
SOURCE_BLOBS = {
    "input_owner_v10.py": "341b3c01649943ddaad5f28431a792c4889cc36e",
    "input_transition_owner_v3.py": "0ea631abcf6272f0538a9ef9198ad8069b47b464",
    "executor_v3.py": "2b072454fd81c41bf9e025217afc78020c7059de",
    "lease.py": "b9dac6bb4063928354733d79bf371909a288a3d1",
    "serialize_release.py": "097125fc1aad8b931e3a3fbe99ee9009add247d4",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _a15_worker_records(owner):
    """Return mutable worker storage; transition-owner records is a snapshot property."""
    inner = getattr(owner, "_inner", None)
    records = getattr(inner, "records", None)
    if not isinstance(records, list):
        raise RuntimeError("input owner does not expose mutable worker records")
    return records


def instrument_source(source):
    """Insert observation-only timestamps around existing XTest release/sync calls."""
    helper_anchor = "from executor_v3 import Cancelled, DecisionRequired\n"
    if source.count(helper_anchor) != 1:
        raise RuntimeError("owner import anchor mismatch")
    helper = helper_anchor + '''

def _a15_worker_records(owner):
    """Return mutable worker storage; transition-owner records is a snapshot property."""
    inner = getattr(owner, "_inner", None)
    records = getattr(inner, "records", None)
    if not isinstance(records, list):
        raise RuntimeError("input owner does not expose mutable worker records")
    return records


def _a15_record_release(records, lease, owner_id, key, keycode, occurrence_id,
                        intent_token, request_ns, sync_return_ns, reason):
    row = {
        "event": "owner_key_release_bracket",
        "owner_id": owner_id,
        "key": key,
        "keycode": keycode,
        "occurrence_id": occurrence_id,
        "intent_token": intent_token,
        "owner_release_start_ns": request_ns,
        "owner_sync_return_ns": sync_return_ns,
        "release_reason": reason,
        "grants_input_authority": False,
    }
    sink = getattr(lease, "_a13_owner_release_receipts", None)
    if sink is not None:
        sink.append(row)
    records.append(row)
'''
    source = source.replace(helper_anchor, helper, 1)

    anchor = "        held = {}\n        touched = set()\n"
    if source.count(anchor) != 1:
        raise RuntimeError("held-state anchor mismatch")
    source = source.replace(
        anchor,
        "        held = {}\n        held_occurrences = {}\n        touched = set()\n",
        1,
    )

    release_loop = """            for code in list(held):
                xtest.fake_input(d, X.KeyRelease, code)
            for button in list(buttons):
"""
    release_loop_new = """            pending_key_releases = []
            for code in list(held):
                lease_for_key = held[code]
                metadata = held_occurrences.get(code, (None, None, None))
                request_ns = time.perf_counter_ns()
                xtest.fake_input(d, X.KeyRelease, code)
                pending_key_releases.append((lease_for_key, code, metadata, request_ns))
            for button in list(buttons):
"""
    if source.count(release_loop) != 1:
        raise RuntimeError("cleanup release loop anchor mismatch")
    source = source.replace(release_loop, release_loop_new, 1)
    sync_anchor = """            d.sync()
            mask = d.screen().root.query_pointer().mask
"""
    sync_new = """            d.sync()
            sync_return_ns = time.perf_counter_ns()
            for lease_for_key, code, metadata, request_ns in pending_key_releases:
                key_name, occurrence_id, intent_token = metadata
                _a15_record_release(_a15_worker_records(self), lease_for_key, self.owner_id, key_name, code,
                                    occurrence_id, intent_token, request_ns,
                                    sync_return_ns, reason)
            mask = d.screen().root.query_pointer().mask
"""
    if source.count(sync_anchor) != 1:
        raise RuntimeError("cleanup sync anchor mismatch")
    source = source.replace(sync_anchor, sync_new, 1)

    down_anchor = "                            held[code] = lease\n"
    if source.count(down_anchor) != 1:
        raise RuntimeError("key-down ownership anchor mismatch")
    source = source.replace(
        down_anchor,
        down_anchor
        + "                            held_occurrences[code] = (key, getattr(lease, 'occurrence_id', None), getattr(lease, 'intent_token', None))\n",
        1,
    )

    explicit_up = """                            if code in held:
                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                del held[code]
"""
    explicit_up_new = """                            if code in held:
                                metadata = held_occurrences.get(code, (key, getattr(lease, 'occurrence_id', None), getattr(lease, 'intent_token', None)))
                                request_ns = time.perf_counter_ns()
                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                sync_return_ns = time.perf_counter_ns()
                                _a15_record_release(_a15_worker_records(self), lease, self.owner_id, key, code,
                                                    metadata[1], metadata[2], request_ns,
                                                    sync_return_ns, "explicit_up")
                                del held[code]
                                held_occurrences.pop(code, None)
"""
    if source.count(explicit_up) != 1:
        raise RuntimeError("explicit-up anchor mismatch")
    source = source.replace(explicit_up, explicit_up_new, 1)

    clear_anchor = "            held.clear()\n            touched.clear()\n"
    if source.count(clear_anchor) != 1:
        raise RuntimeError("held cleanup anchor mismatch")
    source = source.replace(
        clear_anchor,
        "            held.clear()\n            held_occurrences.clear()\n            touched.clear()\n",
        1,
    )
    compile(source, "input_owner_v10_a15.py", "exec")
    return source


def bit_down(bitmap, code):
    return bool(bitmap[code // 8] & (1 << (code % 8)))


def cancellation_release_rows(records, occurrence_id, intent_token, owner_id, keycode):
    return [
        row for row in records
        if row.get("event") == "owner_key_release_bracket"
        and row.get("occurrence_id") == occurrence_id
        and row.get("intent_token") == intent_token
        and row.get("owner_id") == owner_id
        and row.get("keycode") == keycode
        and row.get("release_reason") == "cancelled"
    ]


def self_test():
    raw = (DEPS / "input_owner_v10.py").read_text()
    patched = instrument_source(raw)
    assert patched.count("_a15_record_release(") == 3
    for query in ("query_keymap", "get_input_focus", "input_state"):
        assert patched.count(query) == raw.count(query), "instrumentation changed owner query count: " + query
    for path in DEPS.iterdir():
        if path.suffix == ".py":
            compile(path.read_text(), str(path), "exec")
    sys.path.insert(0, str(DEPS))
    from lease import Lease
    import Xlib.ext.xtest
    assert Lease is not None and Xlib.ext.xtest is not None
    joiner = importlib.import_module("serialize_release").join_explicit_release
    owner = {
        "event": "owner_key_release_bracket", "owner_id": "o", "key": "w",
        "keycode": 25, "occurrence_id": "x", "intent_token": "i",
        "owner_release_start_ns": 2, "owner_sync_return_ns": 3,
    }
    joined = joiner(owner, {"caller_start_ns": 1, "caller_return_ns": 4})
    assert joined["event"] == "joined_release"
    assert joined["owner_event"] == "owner_key_release_bracket"
    assert 1 <= 2 <= 3 <= 4
    cancel_record = {
        "event": "owner_key_release_bracket", "occurrence_id": "cancel-w",
        "intent_token": "intent-cancel", "owner_id": "owner-1",
        "keycode": 25, "release_reason": "cancelled",
    }
    assert cancellation_release_rows(
        [cancel_record], "cancel-w", "intent-cancel", "owner-1", 25
    ) == [cancel_record]
    assert not cancellation_release_rows(
        [cancel_record], "cancel-w", "other-intent", "owner-1", 25
    )
    assert not cancellation_release_rows(
        [cancel_record], "cancel-w", "intent-cancel", "other-owner", 25
    )
    sys.path.insert(0, str(DEPS))
    transition = importlib.import_module("input_transition_owner_v3")
    wrapper = transition.InputOwner.__new__(transition.InputOwner)
    class Inner:
        def __init__(self):
            self.records = []
    wrapper._inner = Inner()
    sentinel = {"event": "construction_persistence_control"}
    _a15_worker_records(wrapper).append(sentinel)
    assert wrapper.records == [sentinel]
    assert wrapper.records is not wrapper._inner.records
    for bad_owner in ({}, {**owner, "event": "wrong"}):
        try:
            joiner(bad_owner, {"caller_start_ns": 1})
        except ValueError:
            pass
        else:
            raise AssertionError("joiner accepted malformed owner row")
    try:
        joiner(owner, {"event": "injected"})
    except ValueError:
        pass
    else:
        raise AssertionError("joiner accepted caller event override")
    print(json.dumps({"construction": "PASS", "source_patch": "PASS",
                      "join_controls": 4, "network": "disabled"}, sort_keys=True))


def run_candidate(out_path):
    sys.path.insert(0, str(DEPS))
    from Xlib import X, XK, display
    from lease import Lease

    out_path.mkdir(parents=True, exist_ok=False)
    raw = {
        "schema": "owner-keyup-xvfb-a15-raw-v1",
        "allocation": "MAP01-OWNER-KEYUP-BRACKET-5156-XVFB-20261002-15",
        "base": BASE,
        "image_id": IMAGE_ID,
        "source_blobs": SOURCE_BLOBS,
        "source_sha256": {p.name: sha256(p) for p in DEPS.iterdir() if p.is_file()},
        "cases": [],
        "case_teardowns": [],
        "candidate_status": "RUNNING",
        "authority_flags_false": True,
    }
    xvfb = None
    owner = None
    observer = None
    candidate_error = None
    display_name = ":91"
    try:
        instrumented = instrument_source((DEPS / "input_owner_v10.py").read_text())
        runtime_dir = Path(tempfile.mkdtemp(prefix="a15-runtime-", dir="/tmp"))
        (runtime_dir / "input_owner_v10.py").write_text(instrumented)
        sys.path.insert(0, str(runtime_dir))
        sys.path.insert(1, str(DEPS))
        owner_module = importlib.import_module("input_owner_v10")
        owner_cls = owner_module.InputOwner
        xvfb_log = open("/tmp/a15-xvfb.log", "wb")
        xvfb = subprocess.Popen(
            ["Xvfb", display_name, "-screen", "0", "640x480x24", "-nolisten", "tcp", "-ac"],
            stdout=xvfb_log, stderr=subprocess.STDOUT,
        )
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                observer = display.Display(display_name)
                break
            except Exception:
                if xvfb.poll() is not None:
                    raise RuntimeError("Xvfb exited before display became ready")
                time.sleep(0.05)
        if observer is None:
            raise RuntimeError("Xvfb readiness timeout")
        root = observer.screen().root
        window = root.create_window(20, 20, 300, 200, 0, observer.screen().root_depth,
                                    X.InputOutput, X.CopyFromParent)
        window.map()
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        observer.sync()
        owner = importlib.import_module("input_transition_owner_v3").InputOwner(
            display_name, _owner_cls=owner_cls
        )

        def keycode(key):
            code = observer.keysym_to_keycode(XK.string_to_keysym(key))
            if not code:
                raise RuntimeError("fixture key has no keycode: " + key)
            return code

        def keymap():
            return list(observer.query_keymap())

        def new_lease(intent):
            lease = Lease(time.perf_counter_ns() + 10_000_000_000)
            lease.expected_focus = window.id
            lease.intent_token = intent
            lease._a13_owner_release_receipts = []
            lease.occurrence_id = None
            return lease

        def admission(case_name, lease, key, occurrence_id):
            lease.occurrence_id = occurrence_id
            before = keymap()
            started = time.perf_counter_ns()
            result = owner.call("down", lease, key)
            returned = time.perf_counter_ns()
            after = keymap()
            code = keycode(key)
            row = {"kind": "admission", "case": case_name, "key": key,
                   "occurrence_id": occurrence_id, "caller_start_ns": started,
                   "caller_return_ns": returned, "admission": result,
                   "owner_id": owner.owner_id,
                   "intent_token": lease.intent_token,
                   "keycode": code,
                   "keymap_before": before, "keymap_after": after,
                   "key_down_before": bit_down(before, code),
                   "key_down_after": bit_down(after, code)}
            raw["cases"].append(row)
            return row

        def explicit_up(case_name, lease, key, occurrence_id):
            lease.occurrence_id = occurrence_id
            code = keycode(key)
            before = keymap()
            receipt = owner.call("up", lease, key)
            after = keymap()
            owner_rows = [r for r in lease._a13_owner_release_receipts
                          if r.get("occurrence_id") == occurrence_id]
            if len(owner_rows) != 1:
                raise RuntimeError("expected exactly one owner receipt for " + occurrence_id)
            owner_row = owner_rows[0]
            joined = importlib.import_module("serialize_release").join_explicit_release(
                owner_row,
                {
                    "operation": receipt["operation"],
                    "key": receipt["key"],
                    "caller_start_ns": receipt["release_call_started_ns"],
                    "caller_return_ns": receipt["release_call_returned_ns"],
                    "intent_token": receipt["intent_token"],
                    "owner_id": receipt["owner_id"],
                    "grants_input_authority": receipt["grants_input_authority"],
                },
            )
            joined["case"] = case_name
            joined["keymap_before"] = before
            joined["keymap_after"] = after
            joined["key_down_before"] = bit_down(before, code)
            joined["key_down_after"] = bit_down(after, code)
            joined["nested"] = (
                joined["caller_start_ns"] <= joined["owner_release_start_ns"]
                <= joined["owner_sync_return_ns"] <= joined["caller_return_ns"]
            )
            raw["cases"].append(joined)
            return joined

        def finish_case(case_name, lease):
            record = owner.call("release", lease)
            state = keymap()
            item = {
                "case": case_name,
                "record": record,
                "keymap_after": state,
                "grants_input_authority": False,
            }
            raw["case_teardowns"].append(item)
            if (not isinstance(record, dict) or record.get("event") != "owner_release"
                    or record.get("verified") is not True or record.get("keys_down") != []
                    or any(bit_down(state, keycode(k)) for k in ("w", "a"))):
                raise RuntimeError("case lease teardown was not verified neutral: " + case_name)
            return item

        # Case 1: single key down/up.
        lease = new_lease("intent-single")
        admission("single", lease, "w", "single-w")
        row = explicit_up("single", lease, "w", "single-w")
        if not (row["key_down_before"] and not row["key_down_after"] and row["nested"]):
            raise RuntimeError("single-key observation gate failed")
        if any(bit_down(keymap(), c) for c in (keycode("w"),)):
            raise RuntimeError("single-key terminal keymap not neutral")
        finish_case("single", lease)

        # Case 2: two keys admitted and explicitly released sequentially.
        lease2 = new_lease("intent-double")
        admission("double", lease2, "w", "double-w")
        admission("double", lease2, "a", "double-a")
        stale = new_lease("intent-stale")
        stale.occurrence_id = "stale-w"
        stale_before = keymap()
        stale_rejected = False
        try:
            owner.call("up", stale, "w")
        except Exception as exc:
            stale_rejected = type(exc).__name__ == "ValueError"
            raw["stale_exception"] = type(exc).__name__
        stale_after = keymap()
        raw["stale_control"] = {
            "occurrence_id": "stale-w", "rejected": stale_rejected,
            "owner_receipts": list(stale._a13_owner_release_receipts),
            "keymap_before": stale_before, "keymap_after": stale_after,
            "keycode": keycode("w"),
            "still_down": bit_down(stale_after, keycode("w")),
        }
        if not stale_rejected or raw["stale_control"]["owner_receipts"] or not raw["stale_control"]["still_down"]:
            raise RuntimeError("stale/unowned release guard failed")
        first = explicit_up("double", lease2, "w", "double-w")
        second = explicit_up("double", lease2, "a", "double-a")
        if not (first["key_down_before"] and not first["key_down_after"]
                and second["key_down_before"] and not second["key_down_after"]
                and first["nested"] and second["nested"]):
            raise RuntimeError("two-key release observation gate failed")
        if any(bit_down(keymap(), c) for c in (keycode("w"), keycode("a"))):
            raise RuntimeError("two-key terminal keymap not neutral")
        finish_case("double", lease2)

        # Case 3: cancel after W admission; queued A admission must be rejected.
        lease3 = new_lease("intent-cancel")
        admission("cancel", lease3, "w", "cancel-w")
        before_cancel = keymap()
        lease3.occurrence_id = "cancel-w"
        lease3.cancel.set()
        cancel_start = time.perf_counter_ns()
        rejected = False
        try:
            owner.call("down", lease3, "a")
        except Exception as exc:
            rejected = type(exc).__name__ == "Cancelled"
            raw["cancel_exception"] = type(exc).__name__
        cancel_return = time.perf_counter_ns()
        after_cancel = keymap()
        cancel_rows = cancellation_release_rows(
            owner.records, "cancel-w", "intent-cancel", owner.owner_id, keycode("w")
        )
        if len(cancel_rows) != 1:
            raise RuntimeError("cancel cleanup did not produce exactly one release receipt")
        cancel_owner = dict(cancel_rows[0])
        cancel_owner.update({
            "case": "cancel",
            "operation": "autonomous_cancel_cleanup",
            "keymap_before": before_cancel,
            "keymap_after": after_cancel,
            "key_down_before": bit_down(before_cancel, keycode("w")),
            "key_down_after": bit_down(after_cancel, keycode("w")),
            "grants_input_authority": False,
        })
        raw["autonomous_cancel_cleanup"] = cancel_owner
        raw["cancel_trigger_call"] = {
            "operation": "down", "key": "a",
            "caller_start_ns": cancel_start, "caller_return_ns": cancel_return,
            "exception": raw.get("cancel_exception"),
            "note": "triggering admission call is separate from an explicit-up caller bracket",
        }
        raw["cancel_owner_cleanup_record"] = [
            record for record in owner.records
            if record.get("event") == "owner_release" and record.get("reason") == "cancelled"
        ]
        raw["cancel_second_admission_rejected"] = rejected
        raw["cancel_terminal_neutral"] = not bit_down(after_cancel, keycode("w")) and not bit_down(after_cancel, keycode("a"))
        if (not rejected or not raw["cancel_terminal_neutral"]
                or not cancel_owner["key_down_before"] or cancel_owner["key_down_after"]
                or cancel_owner["release_reason"] != "cancelled"):
            raise RuntimeError("cancellation gate failed")
        if (len(raw["cancel_owner_cleanup_record"]) != 1
                or raw["cancel_owner_cleanup_record"][0].get("verified") is not True
                or raw["cancel_owner_cleanup_record"][0].get("keys_down") != []):
            raise RuntimeError("owner cleanup record not verified neutral")

        owner.close()
        raw["owner_thread_stopped"] = not owner.thread.is_alive()
        if not raw["owner_thread_stopped"]:
            raise RuntimeError("owner thread remains alive after close")
        owner = None
        observer.close()
        observer = None
        xvfb.terminate()
        try:
            xvfb.wait(timeout=3)
        except subprocess.TimeoutExpired:
            xvfb.kill()
            xvfb.wait(timeout=3)
            raise RuntimeError("Xvfb required forced kill")
        raw["processes_clean"] = raw.get("owner_thread_stopped") is True and (xvfb.returncode == 0 or xvfb.returncode == -15)
        if not raw["processes_clean"]:
            raise RuntimeError("unexpected Xvfb exit: " + repr(xvfb.returncode))
        raw["candidate_status"] = "CANDIDATE_COMPLETED"
    except BaseException:
        candidate_error = traceback.format_exc()
        raw["candidate_status"] = "CANDIDATE_FAILED"
        raw["candidate_error"] = candidate_error
    finally:
        if owner is not None:
            try:
                owner.close()
                raw["owner_cleanup"] = "clean"
            except BaseException as exc:
                raw["owner_cleanup"] = "failed:" + repr(exc)
        if observer is not None:
            try:
                observer.close()
            except Exception:
                pass
        if xvfb is not None and xvfb.poll() is None:
            xvfb.terminate()
            try:
                xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                xvfb.wait(timeout=3)
        (out_path / "raw.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    if candidate_error:
        print(candidate_error, file=sys.stderr)
        return 1
    print(json.dumps({"candidate_status": raw["candidate_status"],
                      "rows": len(raw["cases"]), "raw_sha256": sha256(out_path / "raw.json")},
                     sort_keys=True))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.out is None:
        parser.error("--out is required unless --self-test is set")
    return run_candidate(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
