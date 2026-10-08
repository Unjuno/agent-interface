"""Finite sink-boundary probe for the pinned #59 release-batch backend."""
import subprocess
import sys
import threading
import types

SOURCE_REF = "d6a3fe646d6a8ea92a8688a1f7c54b89261f56f6"
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


def run_case(candidate, failed_position, sink_accepts_before_raise):
    receipts = [{"receipt": i} for i in range(3)]
    rows = []
    for i, receipt in enumerate(receipts):
        rows.append({
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
    emitted = []
    raised = False

    def sink(row):
        nonlocal raised
        if (row.get("release_batch_complete") is True
                and row.get("release_batch_position") == failed_position
                and not raised):
            raised = True
            if sink_accepts_before_raise:
                emitted.append((failed_position, True, "accepted_then_raise"))
            raise OSError("injected sink exception")
        emitted.append((row.get("release_batch_position"),
                        row.get("release_batch_complete"), "delivered"))

    obj.emit = sink
    context = obj._release_batch.context
    try:
        obj._publish_release_batch(context)
    except OSError as error:
        obj._finish_incomplete_release_batch(
            context, error, "publication_exception")
    return emitted


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: probe.py FULL_REPOSITORY_CHECKOUT")
    candidate = load_candidate(sys.argv[1])
    for accepted in (False, True):
        for position in range(3):
            output = run_case(candidate, position, accepted)
            print(f"accept_before_raise={accepted} fail_position={position} "
                  f"observed={output}")


if __name__ == "__main__":
    main()
