import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
freeze = json.loads((out / "FREEZE.json").read_text(encoding="utf-8"))
raw = (out / "RAW.stdout.txt").read_text(encoding="utf-8")
exit_code = int((out / "RAW.exit.txt").read_text(encoding="utf-8"))
run = json.loads((out / "RUN.json").read_text(encoding="utf-8"))
post_run_containers = json.loads((out / "POST-RUN-CONTAINERS.json").read_text(encoding="utf-8"))
checks = {
    "source_hashes_match_freeze": all(
        hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
        for name, digest in freeze["source_sha256"].items()),
    "exit_zero": exit_code == 0,
    "one_test_passed": "Ran 1 test" in raw and "OK" in raw,
    "test_name_observed": "test_cancelled_release_is_published_before_terminal" in raw,
    "run_receipt_matches_raw_and_exit": (
        run["raw_sha256"] == hashlib.sha256((out / "RAW.stdout.txt").read_bytes()).hexdigest()
        and run["exit_code"] == exit_code),
    "no_running_container_after_run": post_run_containers == [],
    "host_cgroup_warning_retained": "does not support swap limit" in raw,
    "network_disabled_and_pinned_image": freeze["limits"]["network"] == "none" and freeze["image"].startswith("sha256:"),
}
result = {"schema": "map01-v39-cancel-release-cause-wslc-c04-audit-v1",
          "checks": checks, "pass": all(checks.values()),
          "scope": "one-shot WSLc portability test; fake Xlib only"}
(out / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
sys.exit(0 if result["pass"] else 1)
