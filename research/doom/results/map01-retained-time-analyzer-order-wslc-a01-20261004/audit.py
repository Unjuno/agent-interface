import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
run = json.loads((ROOT / "RUN.json").read_text(encoding="utf-8-sig"))
raw = (ROOT / run["raw_stdout_stderr"]).read_text(encoding="utf-8-sig")
exit_code = int((ROOT / "EXIT_CODE.txt").read_text(encoding="utf-8-sig").strip())
freeze = (ROOT / "FREEZE.md").read_text(encoding="utf-8-sig")
checks = {
    "retained_stop_exit_1": exit_code == run["exit_code"] == 1 and run["result"] == "STOP",
    "invalid_mount_cause_present": "bind ソースパスは絶対パスである必要があります" in raw,
    "test_process_did_not_start": "Ran 6 tests" not in raw,
    "no_container_created_claim_bound_to_cli_validation": run["container_created"] is False and run["stage"].startswith("WSLc run argument validation"),
    "freeze_records_network_none_and_pull_never": "--pull never --network none" in freeze,
}
result = {"schema": "retained-time-analyzer-wslc-audit-v1", "pass": all(checks.values()), "checks": checks}
(ROOT / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result["pass"] else 1)
