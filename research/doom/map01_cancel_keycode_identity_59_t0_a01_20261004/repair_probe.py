"""Construction follow-up testing keycode identity on input admissions."""
from __future__ import annotations

import hashlib
import json

import probe


OLD = (
    b"result = dict(event='input_admission', key=key, admitted_ns=admitted,\r\n"
    b"                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)"
)
NEW = (
    b"result = dict(event='input_admission', key=key, keycode=code, admitted_ns=admitted,\r\n"
    b"                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)"
)


def run():
    baseline = probe.candidate_source()
    if baseline.count(OLD) != 1:
        raise RuntimeError("frozen admission source mutation is not unique")
    candidate = baseline.replace(OLD, NEW, 1)
    candidate_sha256 = hashlib.sha256(candidate).hexdigest()
    owner_type = probe.load_candidate(candidate)
    arms = [
        probe.run_arm(owner_type, {ord("W"): 87, ord("A"): 65}),
        probe.run_arm(owner_type, {ord("W"): 77, ord("A"): 77}),
    ]
    return {
        "schema": "map01-cancel-keycode-identity-repair-t0-v1",
        "baseline_git_blob": probe.EXPECTED_BLOB,
        "mutation": "add resolved keycode to input_admission receipt",
        "candidate_source_sha256": candidate_sha256,
        "arms": arms,
        "scope": "one-line source mutation under fake Xlib; no live input or game",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
