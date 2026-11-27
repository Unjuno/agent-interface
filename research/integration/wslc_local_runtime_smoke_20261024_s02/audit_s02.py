"""Offline audit for the retained WSLc S02 smoke receipts."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


conditions = read_json("conditions.json")
initial_preflight = read_json("preflight.json")
runtime_preflight = read_json("runtime-preflight.json")
image_pull = read_json("image-pull-attempt-01.json")
runner = read_json("runner-exit.json")
run = ROOT / "run"
cid = (run / "container.cid").read_text(encoding="ascii").strip()
container_name = (run / "container-name.txt").read_text(encoding="utf-8").strip()
sentinel = (run / "sentinel.bin").read_bytes()
run_stdout = (run / "wslc-run.stdout.txt").read_text(encoding="utf-8")
run_stderr = (run / "wslc-run.stderr.txt").read_text(encoding="utf-8")
cleanup_stdout = (run / "wslc-cleanup-query.stdout.txt").read_text(encoding="utf-8")
cleanup_stderr = (run / "wslc-cleanup-query.stderr.txt").read_text(encoding="utf-8")
script_text = (ROOT / "wslc_probe_s02.ps1").read_text(encoding="utf-8")
image_ref = conditions["image"]

checks = {
    "unique_name_preflight_clear": (
        initial_preflight["allocation"]["container_name"] == conditions["allocation"]["container_name"]
        and initial_preflight["allocation"]["name_query_exit"] == 0
        and initial_preflight["allocation"]["name_query_timed_out"] is False
        and initial_preflight["allocation"]["name_query_stdout"] == ""
        and initial_preflight["allocation"]["active_wslc_process_count"] == 0
    ),
    "image_pull_succeeded_at_pinned_digest": (
        image_pull["exit_code"] == 0
        and image_pull["timed_out"] is False
        and image_ref in image_pull["stdout"]
        and initial_preflight["image"]["reference"] == image_ref
        and initial_preflight["image"]["inspect_exit"] == 1
    ),
    "post_pull_image_inspect_exact_digest": (
        runtime_preflight["exact_image_inspect"]["exit"] == 0
        and image_ref in runtime_preflight["exact_image_inspect"]["stdout"]
    ),
    "runner_used_exact_preflight_name_and_bounded_flags": (
        runner["exit_code"] == 0
        and runner["container_name"] == container_name
        and container_name == conditions["allocation"]["container_name"]
        and runtime_preflight["container_name"] == container_name
        and f"$containerName = '{container_name}'" in script_text
        and "'--name'," in script_text
        and "'--pull', 'never'" in script_text
        and "'none', '--memory', '512M', '--cpus', '1'" in script_text
        and "${probePath}:/probe:ro" in script_text
        and "'--rm'" in script_text
        and runtime_preflight["active_wslc_process_count"] == 0
    ),
    "full_container_id_retained": re.fullmatch(r"[0-9a-f]{64}", cid) is not None,
    "read_only_probe_effect_observed": (
        sentinel == b"wslc-readonly-probe"
        and "read-only bind mount: PASS (EROFS)" in run_stdout
        and "must-not-write" not in sentinel.decode("ascii")
    ),
    "exact_cid_cleanup_query_succeeded_empty": (
        "--filter" in script_text
        and "id=$ContainerId" in script_text
        and cleanup_stdout == ""
        and cleanup_stderr == ""
        and runner["exit_code"] == 0
    ),
    "memory_limit_not_overclaimed": "swap limit capabilities" in run_stderr,
}

files = [
    ".gitattributes",
    "RESULT.md",
    "conditions.json",
    "conditions-amendment-01.json",
    "preflight.json",
    "runtime-preflight.json",
    "image-pull.json",
    "image-pull-attempt-01.json",
    "runner-console.txt",
    "runner-exit.json",
    "wslc_probe_s02.ps1",
    "wslc_bounded_process.psm1",
    "audit_s02.py",
    "run/container-name.txt",
    "run/container.cid",
    "run/sentinel.bin",
    "run/wsl-version.stdout.txt",
    "run/wsl-version.stderr.txt",
    "run/wslc-version.stdout.txt",
    "run/wslc-version.stderr.txt",
    "run/wslc-run.stdout.txt",
    "run/wslc-run.stderr.txt",
    "run/wslc-cleanup-query.stdout.txt",
    "run/wslc-cleanup-query.stderr.txt",
]
hashes = {
    name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    for name in files
}
result = {
    "schema": "wslc-local-runtime-smoke-s02-audit-v1",
    "audited_at_utc": datetime.now(timezone.utc).isoformat(),
    "attempt_id": conditions["attempt_id"],
    "scope": conditions["scope"],
    "checks": checks,
    "passed": all(checks.values()),
    "cid_sha256": hashlib.sha256(cid.encode("ascii")).hexdigest(),
    "receipt_sha256": hashes,
}
with (ROOT / "audit.json").open("w", encoding="utf-8", newline="\n") as audit_file:
    audit_file.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"passed": result["passed"], "checks": checks}, indent=2, sort_keys=True))
if not result["passed"]:
    raise SystemExit(1)
