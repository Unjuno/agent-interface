import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
sources = [
    "research/live_control/test_executor_owner_cancel_cause_v1.py",
    "research/live_control/executor_v12.py",
    "research/live_control/executor_v5.py",
    "research/live_control/executor_v11.py",
    "research/live_control/executor_v3.py",
    "research/live_control/lease_release_v1.py",
    "research/live_control/lease_cause_v2.py",
    "research/live_control/lease_cause_v1.py",
    "research/live_control/lease.py",
    "research/live_control/input_transition_owner_v4.py",
    "research/live_control/input_owner_v12.py",
]
repo = str(root).replace("\\", "/")
freeze = {
    "run_id": "MAP01-V39-CANCEL-RELEASE-CAUSE-WSLC-C04-20261004",
    "classification": "one-shot CPU-only construction portability check; not a live/formal allocation",
    "base_commit": "5934eebb2534709a8a5d282b8d1f001e6ff9eb64",
    "wslc": "3.0.1.0",
    "resource_snapshot": "wslc container list --format json returned no running containers immediately before freeze",
    "image": "sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378",
    "limits": {"network": "none", "cpus": 1, "memory": "512M", "source_mount": "read-only"},
    "command": f'wslc run --rm --pull never --network none --cpus 1 --memory 512M --volume "{repo}:/src:ro" --workdir /src sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378 python -B research/live_control/test_executor_owner_cancel_cause_v1.py',
    "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                      for name in sources},
    "decision": "PASS iff run exits zero, exactly one unittest passes and output ends OK; otherwise FAIL/HOLD",
    "max_runs": 1,
    "retry": "none",
    "scope": "fake Xlib and deterministic owner dequeue/dispatch schedule only; no game, model, GUI, physical input or scorer",
}
(out / "FREEZE.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
print((out / "FREEZE.json").read_text(encoding="utf-8"))
