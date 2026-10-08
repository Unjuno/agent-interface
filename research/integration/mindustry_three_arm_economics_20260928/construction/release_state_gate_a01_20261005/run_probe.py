from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import types
from pathlib import Path

COMMIT = "8ff7afed76c1d81eabac9d0c37d4191b352045a4"
SOURCE_BLOB = "ffaa64cb04f0457c11e52393b32a5ba9b2b733b0"
SOURCE_PATH = "research/integration/mindustry_three_arm_economics_20260928/target_socket_submit_v1.py"


def response(action: str, release: object) -> dict:
    return {
        "authority": "none",
        "acknowledgement": "not implied",
        "command_receipt": {
            "request_id": action,
            "state": "stdin_flushed",
            "replayed": False,
        },
        "records": [{
            "event": "terminal",
            "id": action,
            "status": "completed",
            **({} if release is MISSING else {"release": release}),
        }],
        "status": "boundary",
        "cursor": 1,
    }


class _Missing:
    pass


MISSING = _Missing()


def main() -> int:
    source = subprocess.check_output(["git", "cat-file", "blob", SOURCE_BLOB])
    module = types.ModuleType("pinned_target_socket_submit_v1")
    module.__file__ = f"{COMMIT}:{SOURCE_PATH}"
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    cases = [
        ("explicit_empty_control", {"verified": True, "keys_down": [], "buttons_down": []}),
        ("held_key", {"verified": True, "keys_down": ["LEFT"], "buttons_down": []}),
        ("held_button", {"verified": True, "keys_down": [], "buttons_down": ["left"]}),
        ("missing_keys_down", {"verified": True, "buttons_down": []}),
        ("missing_buttons_down", {"verified": True, "keys_down": []}),
        ("verified_false", {"verified": False, "keys_down": [], "buttons_down": []}),
        ("missing_release", MISSING),
    ]
    rows = []
    for case_id, release in cases:
        action = "A01-" + case_id
        sink_rows = []
        submitter = module.TargetSocketSubmitter("in-memory://unused", trace_sink=sink_rows.append)
        submitter._exchange = lambda _request, a=action, r=release: response(a, r)
        try:
            result = submitter({"op": "submit", "id": action})
        except Exception as error:
            rows.append({"case": case_id, "outcome": "rejected", "error_type": type(error).__name__, "receipt": None})
        else:
            rows.append({"case": case_id, "outcome": "accepted", "error_type": None, "receipt": result})
    result = {
        "source_commit": COMMIT,
        "source_path": SOURCE_PATH,
        "source_git_blob": SOURCE_BLOB,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "python": sys.version,
        "cases": rows,
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
