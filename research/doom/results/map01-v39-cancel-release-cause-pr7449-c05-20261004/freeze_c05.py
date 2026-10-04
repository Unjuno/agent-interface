import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
head = "a6da76741c91d8cfa0f035445c1fd6b8b864560e"
source_path = "research/live_control/input_owner_v12.py"
test_path = "research/doom/results/map01-v39-cancel-release-cause-c02-20261004/test_cancel_release_cause.py"
source = subprocess.check_output(["git", "show", f"{head}:{source_path}"], cwd=root)
test = (root / test_path).read_bytes()
(out / "PR-SOURCE-input_owner_v12.py").write_bytes(source)
freeze = {
    "run_id": "MAP01-V39-CANCEL-RELEASE-CAUSE-PR7449-C05-20261004",
    "classification": "one-shot fake-Xlib construction reproduction on a frozen PR source; not a live allocation",
    "pr": 7449,
    "pr_head": head,
    "source_path": source_path,
    "source_sha256": hashlib.sha256(source).hexdigest(),
    "source_git_blob": subprocess.check_output(
        ["git", "rev-parse", f"{head}:{source_path}"], cwd=root, text=True).strip(),
    "frozen_test_path": test_path,
    "frozen_test_sha256": hashlib.sha256(test).hexdigest(),
    "command": "python -B research/doom/results/map01-v39-cancel-release-cause-c02-20261004/test_cancel_release_cause.py",
    "environment": {"OWNER_UNDER_TEST": "PR-SOURCE-input_owner_v12.py"},
    "decision": "PASS for the defect hypothesis iff forced cancellation fails only by release-vs-cancelled and ordinary release control passes",
    "max_runs": 1,
    "retry": "none",
    "scope": "actual owner thread with fake Xlib and forced after-dequeue-before-dispatch cancellation; no game/GUI/model/physical input",
}
(out / "FREEZE.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
print(json.dumps(freeze, indent=2, sort_keys=True))
