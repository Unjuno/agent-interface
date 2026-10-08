"""Read-only validation of frozen red/green outcomes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
checks = {
    "runner_frozen": digest(ROOT / "run.py") == freeze["runner_sha256"],
    "test_frozen": digest(ROOT / "test_finish_send_failure_wait.py") == freeze["test_sha256"],
    "baseline_frozen": digest(ROOT / "baseline/doom_controller_failure_cleanup_v1.py") == freeze["red_source_sha256"],
    "candidate_frozen": digest(ROOT / "candidate/doom_controller_failure_cleanup_v1.py") == freeze["green_source_sha256"],
    "red_failed_as_expected": (ROOT / "red-run/exit-code.txt").read_text().strip() == "1" and "cleanup waited for the child after finish send failed" in (ROOT / "red-run/stderr.bin").read_text(errors="replace"),
    "green_passed": (ROOT / "green-run/exit-code.txt").read_text().strip() == "0" and "Ran 1 test" in (ROOT / "green-run/stderr.bin").read_text(errors="replace") and "OK" in (ROOT / "green-run/stderr.bin").read_text(errors="replace"),
    "raw_captured": all((ROOT / phase / name).is_file() for phase in ("red-run", "green-run") for name in ("argv.json", "stdout.bin", "stderr.bin", "exit-code.txt")),
}
status = "PASS_FROZEN_RED_GREEN" if all(checks.values()) else "FAIL_AUDIT"
result = {"status": status, "checks": checks, "scope": "saved freeze/raw audit only; no rerun"}
(ROOT / "audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
