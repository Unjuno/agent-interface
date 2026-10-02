"""Independent raw-only audit for one v6 zero-fit Docker construction run."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
receipt = json.loads((HERE / "construction_receipt.json").read_text(encoding="utf-8"))
raw_path = HERE / receipt["raw_stdout_path"]
raw_bytes = raw_path.read_bytes()
raw = raw_bytes.decode("utf-8")
errors: list[str] = []


def require(condition: bool, name: str) -> None:
    if not condition:
        errors.append(name)


freeze = json.loads((ROOT / "CONSTRUCTION_FREEZE.json").read_text(encoding="utf-8"))
protocol = (ROOT / "protocol.py").read_text(encoding="utf-8")
expected_image = re.search(r'^IMAGE_ID = "([^"]+)"$', protocol, re.MULTILINE)
require(receipt.get("schema") == "needle-v6-docker-stage0-receipt-v1", "receipt_schema")
require(receipt.get("allocation") == freeze.get("allocation"), "allocation_binding")
require(receipt.get("branch_head") == "d32a771ac9aa090fc39ff596c55e75484f437dc5", "branch_head")
require(receipt.get("image_id") == freeze.get("image_id", receipt.get("image_id")), "image_id_receipt")
require(bool(expected_image) and receipt.get("image_id") == expected_image.group(1), "frozen_image_binding")
require(receipt.get("image_platform") == "linux/amd64", "image_platform")
require("network=none" in receipt["argv"] and "--read-only" in receipt["argv"], "sandbox_flags")
require("--pull=never" in receipt["argv"], "no_pull")
require(receipt["argv"][-5:] == ["-B", "-m", "unittest", "-v", "test_protocol.py"], "construction_only_entrypoint")
require(receipt.get("runner_invocations") == 1, "single_runner")
require(receipt.get("docker_exit_code") == 0, "runner_exit")
require(receipt.get("construction_seed_accessed") is False, "construction_seed_unused")
require(receipt.get("formal_seed_accessed") is False, "formal_seed_unused")
require(receipt.get("optimizer_steps") == 0 and receipt.get("model_forward_calls") == 0, "zero_fit_scope")
require(hashlib.sha256(raw_bytes).hexdigest() == receipt.get("raw_stdout_sha256"), "raw_sha256")

source = receipt.get("source_mount", "")
expected_mount = f"type=bind,source={source},target=/src,readonly"
expected_argv = [
    "run", "--rm", "--pull=never", "--platform=linux/amd64", "--network=none",
    "--read-only", "--cpus=1", "--memory=2g", "--pids-limit=64", "--tmpfs",
    "/tmp:rw,nosuid,nodev,size=256m", "--entrypoint=python", "--mount", expected_mount,
    "--workdir=/src", receipt["image_id"], "-B", "-m", "unittest", "-v", "test_protocol.py",
]
require(receipt.get("argv") == expected_argv, "argv_exact")
match = re.search(r"^ARGV_JSON=(.+)$", raw, re.MULTILINE)
try:
    raw_argv = json.loads(match.group(1)) if match else None
except (json.JSONDecodeError, TypeError):
    raw_argv = None
require(raw_argv == receipt.get("argv"), "argv_receipt_raw_match")
require(f"FROZEN_BRANCH={receipt.get('branch_head')}" in raw, "raw_branch_binding")
require(f"CURRENT_MAIN={receipt.get('main_at_run')}" in raw, "raw_main_binding")
require(f"DOCKER_EXIT_CODE={receipt.get('docker_exit_code')}" in raw, "raw_exit_binding")
test_lines = re.findall(r"^(test_[^(]+\(test_protocol\.[^)]+\)) \.\.\.", raw, re.MULTILINE)
require(len(test_lines) == 27 and len(set(test_lines)) == 27, "unique_test_count")
status_lines = re.findall(r"(?:\.\.\. ok|^ok)$", raw, re.MULTILINE)
require(len(status_lines) == 27, "test_status_lines")
require("Ran 27 tests in 2.308s" in raw and "\nOK\n" in raw, "unittest_summary")
require("FAILED" not in raw and "ERROR:" not in raw, "no_test_failures")

source_errors = []
for rel, digest in freeze.get("source_sha256", {}).items():
    source_file = ROOT / rel
    if not source_file.is_file() or hashlib.sha256(source_file.read_bytes()).hexdigest() != digest:
        source_errors.append(rel)
require(not source_errors, "frozen_source_hashes")

result = {
    "schema": "needle-v6-docker-stage0-independent-audit-v1",
    "decision": "PASS_DOCKER_CONSTRUCTION_FIXTURES_ONLY" if not errors else "HOLD_AUDIT_INTEGRITY",
    "checks": 25,
    "errors": errors,
    "raw_stdout_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    "tests_observed": len(test_lines),
    "source_hash_mismatches": source_errors,
}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
raise SystemExit(0 if not errors else 1)
