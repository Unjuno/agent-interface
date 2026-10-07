"""Six-case position/delivery-mode validation of the pinned #7638 candidate."""
import json
import subprocess
import sys
import threading
import types

SOURCE_REF = "1030a47894cb4f30a8c92bd577432e7962560741"
SOURCE_PATH = "research/doom/doom_owner_thread_release_batch_backend_v1.py"


def load_candidate(repository):
    base = types.ModuleType("doom_typed_release_backend_v2")
    base.Backend = object
    base.suite = object()
    owner = types.ModuleType("input_transition_owner_v4")
    owner.InputOwner = object
    sys.modules[base.__name__] = base
    sys.modules[owner.__name__] = owner
    module = types.ModuleType("candidate")
    source_ref = f"{SOURCE_REF}:{SOURCE_PATH}"
    blob = subprocess.check_output(
        ["git", "-C", repository, "rev-parse", source_ref], text=True
    ).strip()
    source = subprocess.check_output(
        ["git", "-C", repository, "show", source_ref], text=True
    )
    print(f"source_ref={SOURCE_REF} source_path={SOURCE_PATH} blob={blob}")
    exec(compile(source, source_ref, "exec"), module.__dict__)
    return module


class Lease:
    intent_token = "T"


class Owner:
    owner_id = "O"

    def __init__(self, receipts):
        self.records = [
            {"event": "owner_explicit_keyup", "owner_thread_keyup_receipt": row}
            for row in receipts
        ]

    def call(self, operation):
        assert operation == "input_state"
        return {"owner_id": "O", "sample_started_ns": 1000,
                "sample_finished_ns": 1010, "owned_keycodes": []}


def run_case(candidate, failed_position, accepted_before_raise):
    receipts = [{"receipt": i} for i in range(3)]
    rows = []
    for i, receipt in enumerate(receipts):
        rows.append({
            "event": "input_release_transition", "key": chr(97 + i),
            "owner_id": "O", "intent_token": "T",
            "release_call_started_ns": 10 + i * 10,
            "release_call_returned_ns": 15 + i * 10,
            "backend_owned_before_release": True,
            "ordinary_release_candidate": True,
            "owner_thread_keyup_verified": True,
            "owner_thread_keyup_receipt": receipt,
            "owner_cleanup_record_count_before_release": i,
            "release_batch_identifier": "B", "release_batch_step": 0,
            "id": "B", "step": 0,
        })
    obj = object.__new__(candidate.Backend)
    obj._release_batch = threading.local()
    obj._release_batch.context = {"rows": rows, "identifier": "B", "step": 0}
    obj.owner = Owner(receipts)
    obj.lease = Lease()
    obj._last_release_batch_delivery = None
    observed = []
    raised = False

    def sink(row):
        nonlocal raised
        if (row.get("release_batch_complete") is True
                and row.get("release_batch_position") == failed_position
                and not raised):
            raised = True
            if accepted_before_raise:
                observed.append({"position": failed_position,
                                 "sink_accept": "accepted_then_raise"})
            raise OSError("injected sink failure")
        observed.append({
            "position": row.get("release_batch_position"),
            "sink_accept": "returned",
            "complete": row.get("release_batch_complete"),
        })

    obj.emit = sink
    context = obj._release_batch.context
    try:
        obj._publish_release_batch(context)
    except OSError as error:
        obj._finish_incomplete_release_batch(
            context, error, "publication_exception")
    return {
        "accept_before_raise": accepted_before_raise,
        "failed_position": failed_position,
        "ledger": obj._last_release_batch_delivery,
        "observed": observed,
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: probe.py FULL_REPOSITORY_CHECKOUT")
    candidate = load_candidate(sys.argv[1])
    for accepted in (False, True):
        for position in range(3):
            print(json.dumps(run_case(candidate, position, accepted), sort_keys=True))


if __name__ == "__main__":
    main()
