import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
source_paths = [
    "research/live_control/input_owner_v12.py",
    "research/live_control/input_transition_owner_v4.py",
    "research/live_control/input_transition_owner_v3.py",
    "research/live_control/executor_v12.py",
    "research/live_control/executor_v5.py",
    "research/live_control/executor_v11.py",
    "research/live_control/executor_v3.py",
    "research/live_control/lease_release_v1.py",
    "research/live_control/lease_cause_v2.py",
    "research/live_control/lease_cause_v1.py",
    "research/live_control/lease.py",
    "research/live_control/test_executor_owner_cancel_cause_v1.py",
]
tests = [
    "research/doom/results/map01-v39-cancel-release-cause-pr7449-c05-20261004/FROZEN-C02-test.py",
    "research/live_control/test_executor_owner_cancel_cause_v1.py",
]
freeze = {
    "run_id": "MAP01-V39-CANCEL-RELEASE-CAUSE-PR7449-C06-20261004",
    "classification": "local regression construction on PR #7449 source; no live allocation",
    "base_pr_head": "a6da76741c91d8cfa0f035445c1fd6b8b864560e",
    "python": "CPython 3.11.9 Windows host",
    "source_sha256": {p: hashlib.sha256((root / p).read_bytes()).hexdigest()
                       for p in source_paths},
    "test_sha256": {p: hashlib.sha256((root / p).read_bytes()).hexdigest()
                    for p in tests},
    "pre_fix_snapshot_sha256": hashlib.sha256((root / "research/doom/results/map01-v39-cancel-release-cause-pr7449-c05-20261004/PR-SOURCE-input_owner_v12.py").read_bytes()).hexdigest(),
    "expected_delta": "exact PR #7449 owner v12 except explicit release cause is cancelled when same active lease cancel is set at dispatch",
    "commands": [
        "OWNER_UNDER_TEST=<repo>/research/live_control/input_owner_v12.py python -B research/doom/results/map01-v39-cancel-release-cause-pr7449-c05-20261004/FROZEN-C02-test.py",
        "python -B research/live_control/test_executor_owner_cancel_cause_v1.py",
    ],
    "decision": "PASS iff each command exits zero and all scoped assertions pass",
    "max_runs_per_command": 1,
    "retry": "none unless a code/test defect requires normal regression repair; no formal allocation is involved",
    "scope": "fake Xlib, deterministic dequeue/dispatch schedule, minimal backend; no game/model/GUI/physical input",
}
(out / "FREEZE.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
print(json.dumps(freeze, indent=2, sort_keys=True))
