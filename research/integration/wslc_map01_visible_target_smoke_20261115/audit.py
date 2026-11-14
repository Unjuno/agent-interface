"""Audit the retained no-input WSLc MAP01 target smoke packet."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parent


def require(condition, message):
    if not condition:
        raise SystemExit(message)


for name in ("conditions.json", "conditions-a02.json", "conditions-a03.json"):
    json.loads((ROOT / name).read_text(encoding="utf-8"))

require((ROOT / "exit-code.txt").read_text().strip() == "1",
        "A01 exit code changed")
require("read-only file system" in
        (ROOT / "stderr.raw.txt").read_text(encoding="utf-8"),
        "A01 init failure receipt missing")
require((ROOT / "exit-code-a02.txt").read_text().strip() == "137",
        "A02 bounded-stop exit code changed")
require((ROOT / "stdout-a02.raw.txt").stat().st_size == 0,
        "A02 unexpectedly recorded application progress")
require((ROOT / "exit-code-a03.txt").read_text().strip() == "0",
        "A03 did not exit successfully")

lines = (ROOT / "stdout-a03.raw.txt").read_text(encoding="utf-8").splitlines()
records = [json.loads(line) for line in lines]
phases = [row["phase"] for row in records if "phase" in row]
result = next(row for row in records if row.get("status"))
require(phases == ["python_and_vizdoom_imported",
                   "configuration_complete_before_init", "init_complete",
                   "new_episode_complete", "initial_state_received",
                   "game_closed_normally"], "A03 phase order changed")
require(result["status"] == "PASS_TARGET_STARTUP_NO_INPUT",
        "A03 target startup did not pass")
require(result["map"] == "MAP01" and result["input_events_sent"] == 0,
        "A03 scope changed")
require(result["screen_shape"] == [3, 480, 640],
        "A03 frame shape changed")

expected = {}
for line in (ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    digest, name = line.split("  ", 1)
    expected[name] = digest
actual_names = {path.name for path in ROOT.iterdir()
                if path.is_file() and path.name != "SHA256SUMS"}
require(set(expected) == actual_names, "manifest membership changed")
for name, digest in expected.items():
    actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    require(actual == digest, f"SHA-256 mismatch: {name}")

print(json.dumps({"status": "PASS_PACKET_AUDIT",
                  "manifest_entries": len(expected),
                  "A01": "FAIL_PREINPUT_CONTAINER_INIT",
                  "A02": "FAIL_PREINPUT_STARTUP_TIMEOUT",
                  "A03": "PASS_TARGET_STARTUP_NO_INPUT",
                  "claims_about_input": False}, sort_keys=True))
