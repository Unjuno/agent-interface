"""Reproduce lease-object identity reuse against a pinned wrapper source."""
import argparse
import gc
import importlib.util
import json
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from unittest import mock
import types

SOURCE_PATH = "research/live_control/input_transition_owner_v3.py"
DEFAULT_REF = "cf4904c678830ebe1de84ec34c07df01f8be8b34"


class FakeInner:
    def __init__(self, _display_name):
        self.owner_id = "fake-owner"
        self.records = []
        self.result = None

    def call(self, operation, _lease=None, _key=None):
        if operation == "down":
            return {
                "event": "input_admission",
                "key": "w",
                "admitted_ns": 80,
                "input_ack_ns": 90,
            }
        return self.result

    def close(self):
        return None


class Lease:
    def __init__(self):
        self.intent_token = "synthetic-intent"
        self.deadline = 10**30
        self.cancel = threading.Event()
        self.focus_invalid = False


def load_source(args):
    if args.source_file:
        source_path = Path(args.source_file)
        try:
            identity = source_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            identity = source_path.name
        return source_path.read_bytes(), identity
    blob = subprocess.check_output(
        ["git", "show", f"{args.git_ref}:{SOURCE_PATH}"]
    )
    return blob, f"{args.git_ref}:{SOURCE_PATH}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--git-ref", default=DEFAULT_REF)
    parser.add_argument("--source-file")
    args = parser.parse_args()
    source, source_id = load_source(args)

    base = types.ModuleType("input_owner_v10")
    base.InputOwner = FakeInner
    previous = sys.modules.get("input_owner_v10")
    sys.modules["input_owner_v10"] = base
    try:
        with tempfile.TemporaryDirectory() as temporary:
            module_path = Path(temporary) / "input_transition_owner_v3.py"
            module_path.write_bytes(source)
            spec = importlib.util.spec_from_file_location("candidate", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            owner = module.InputOwner(":fake", _owner_cls=FakeInner)
            old_lease = Lease()
            new_lease = Lease()
            with mock.patch.object(module, "id", return_value=41, create=True):
                owner.call("down", old_lease, "w")
                owner._inner.result = None
                with mock.patch.object(
                    module.time, "perf_counter_ns", side_effect=[100, 140]
                ):
                    result = owner.call("up", new_lease, "w")
            report = {
                "source": source_id,
                "source_bytes_sha256": __import__("hashlib").sha256(source).hexdigest(),
                "distinct_lease_objects": old_lease is not new_lease,
                "new_lease_had_no_admission": True,
                "forced_id_collision": True,
                "owner_release_history_complete": result["owner_release_history_complete"],
                "ordinary_release_candidate": result["ordinary_release_candidate"],
            }
    finally:
        if previous is None:
            del sys.modules["input_owner_v10"]
        else:
            sys.modules["input_owner_v10"] = previous

    class Small:
        pass

    first = Small()
    first_id = id(first)
    del first
    gc.collect()
    natural_reuse_attempts = None
    for attempt in range(1, 10001):
        candidate = Small()
        if id(candidate) == first_id:
            natural_reuse_attempts = attempt
            break
        del candidate
    report["bounded_natural_id_reuse"] = natural_reuse_attempts is not None
    report["natural_id_reuse_attempts"] = natural_reuse_attempts
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
