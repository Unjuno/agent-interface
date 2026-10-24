from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
repo = root.parents[2]
load = lambda p: json.loads((root / p).read_text(encoding="utf-8-sig"))
pre = load("PREREGISTRATION.json")
cond = load("CONDITIONS.json")
invocation = load("INVOCATION-METADATA.json")
result = load("output/result.json")
setup = load("output/container-setup.json")
checks: dict[str, bool] = {}


def check(name: str, value: bool) -> None:
    checks[name] = bool(value)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


check(
    "attempt_source_pins_match",
    pre["attempt_id"] == cond["attempt_id"] == invocation["attempt_id"]
    == "wslc-standard-caller-xvfb-20261025-r38"
    and pre["source_commit"] == cond["source_commit"],
)
for rel, digest in pre["source_hashes"].items():
    check("source_raw_sha_" + rel.replace("/", "_"), sha(repo / rel) == digest)
    tree = subprocess.run(
        ["git", "rev-parse", f'{pre["source_commit"]}:{rel}'],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    work = subprocess.run(
        ["git", "hash-object", "--path=" + rel, rel],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    check(
        "source_commit_blob_" + rel.replace("/", "_"),
        tree.returncode == work.returncode == 0
        and tree.stdout.strip() == work.stdout.strip(),
    )

output = root / "output"
state = (output / "container-state-before-cleanup.txt").read_text()
mounts = (output / "container-mounts-before-cleanup.txt").read_text().splitlines()
check(
    "pinned_image_digest",
    pre["image"] in (output / "pinned-image-inspect.txt").read_text()
    and pre["image"] in state,
)
check(
    "no_network_resource_limits",
    " none " in state
    and "2147483648" in state
    and "2000000000" in state
    and "128" in state,
)
check(
    "mounts_readonly_except_output",
    all(f"{p}:readonly=true" in mounts for p in ["/repo", "/deps", "/stage", "/xkb"])
    and "/out:readonly=false" in mounts,
)
check("tmpfs_exec", "rw,exec,nosuid,nodev,mode=1777,size=512m" in state)
check(
    "preflight_before_trial",
    (output / "preflight-status.txt").read_text().strip() == "pass"
    and "local_xres_identity=" in (output / "xvfb-process-identity-preflight.txt").read_text()
    and (output / "trial-started.txt").exists(),
)
runner_log = (output / "runner.stderr.txt").read_text()
check(
    "test_and_runner_exit_zero",
    (output / "docker-run-exit-code.txt").read_text().strip() == "0"
    and (output / "test-exit-code.txt").read_text().strip() == "0"
    and setup.get("returncode") == 0
    and "Ran 1 test" in runner_log
    and "\nOK\n" in runner_log,
)
pause = result["xvfb_server_pause"]
check(
    "requested_pause_pidfd_resume",
    pause["requested_pause_ms"] == 3600
    and pause["observed_pause_ms"] >= 3600
    and pause["signal_identity"] == "retained_pidfd"
    and pause["resume_receipt"]["error"] is None,
)
check("public_cancel_bound", result["cancel_elapsed_ms"] < 3000)
tx = result["cancel"]["cancellation"]
start = tx["admitted_monotonic_ns"]
deadline = tx["transaction_deadline_monotonic_ns"]
released = result["independent_release_readback"]["owner_release_attempt"]["release"][
    "readback_monotonic_ns"
]
check("exact_4s_transaction", deadline - start == 4_000_000_000)
check(
    "release_readback_before_deadline",
    result["independent_release_readback"]["owner_release_attempt"]["status"]
    == "readback_verified"
    and result["independent_release_readback"]["owner_release_attempt"]["release"][
        "verified"
    ]
    is True
    and released <= deadline,
)
check(
    "independent_readback_5s",
    (result["independent_release_readback"]["observed_ns"]
     - result["timing_ns"]["cancel_started"]) / 1e6 <= 5000
    and result["independent_release_readback"]["keys_down"] == {"a": False, "b": False},
)
horizon = result["late_request_horizon_readback"]
check(
    "late_horizon_clear",
    horizon["ms_after_cancel_start"] >= 8500
    and horizon["late_keypress_b_observed"] is False
    and horizon["keys_down"] == {"a": False, "b": False, "c": False},
)
old = result["independent_task_oracle"]
fresh = result["fresh_session_recovery"]["task_oracle"]
check(
    "old_task_oracle_pass",
    result["counted_task_outcomes"]["old_task"] == "pass"
    and old["status"] == "pass"
    and all(old["checks"].values()),
)
check(
    "fresh_task_exact_once_pass",
    result["counted_task_outcomes"]["fresh_task"] == "pass"
    and fresh["status"] == "pass"
    and fresh["task_success"] is True
    and all(fresh["checks"].values())
    and result["fresh_session_recovery"]["effect_count_before_input"] == [0]
    and result["fresh_session_recovery"]["effect_count_after_input"] == [1]
    and result["fresh_session_recovery"]["effect_count_at_horizon"] == [1],
)
check(
    "old_unknown_fence_preserved",
    fresh["checks"]["old_unknown_fence_preserved"]
    and fresh["checks"]["old_fence_unchanged_after_fresh_task"]
    and result["fresh_session_recovery"]["old_cancellation_fence"]["cleanup_status"]
    == "UNKNOWN"
    and result["fresh_session_recovery"]["old_cancellation_fence"]["replay_allowed"]
    is False,
)
check(
    "runtime_unknown_not_upgraded",
    result["cancel"]["cleanup_status"] == "UNKNOWN"
    and result["cancel"]["release_confirmed"] is False
    and result["cancel"]["replay_allowed"] is False
    and result["cancel"]["task_success"] is None,
)
check(
    "xvfb_stopped",
    (output / "xvfb-process-absent-after-run.txt").read_text().strip().lower() == "true",
)
inspect_text = (output / "container-inspect-after-cleanup.txt").read_text().lower()
check(
    "docker_container_removed",
    (output / "docker-cleanup-exit-code.txt").read_text().strip() == "0"
    and (output / "container-inspect-after-cleanup-exit-code.txt").read_text().strip() != "0"
    and "no such container" in inspect_text,
)

stage = json.loads(
    (repo / "research/integration/wslc_standard_caller_xvfb_20261025_r33/STAGE-MANIFEST.json")
    .read_text(encoding="utf-8-sig")
)
stage_root = repo / "research/integration/wslc_standard_caller_xvfb_20261025_r16/stage"
check(
    "stage_manifest_all_files_match",
    len(stage) == 1252 and all(sha(stage_root / row["path"]) == row["sha256"] for row in stage),
)
xkb = json.loads(
    (repo / "research/integration/wslc_standard_caller_xvfb_20261025_r34/xkb-materialization.json")
    .read_text(encoding="utf-8-sig")
)
xkb_root = repo / "research/integration/wslc_standard_caller_xvfb_20261025_r34/xkb-materialized"
check(
    "xkb_materialization_all_files_match",
    xkb["files"] == 293
    and all(sha(xkb_root / row["path"]) == row["sha256"] for row in xkb["manifest"]),
)

classification = "PASS_SCOPED_4S_TRANSACTION_3600MS" if all(checks.values()) else "STOP_OR_FAIL"
tx_ms = (tx["completed_monotonic_ns"] - start) / 1e6
margin_ms = (deadline - released) / 1e6
parent_ms = (
    result["independent_release_readback"]["observed_ns"] - result["timing_ns"]["cancel_started"]
) / 1e6
fresh_latency = result["fresh_session_recovery"]["effect_timing_ms"][
    "input_invocation_to_effect_readback_completed"
]
raw = []
for path in sorted(root.rglob("*")):
    if path.is_file() and path.name not in {
        "AUDIT.json", "AUDIT-EXECUTION.log", "RESULT.md", "OUTCOME.json"
    }:
        raw.append(
            {
                "path": path.relative_to(repo).as_posix(),
                "sha256": sha(path),
                "bytes": path.stat().st_size,
            }
        )
report = {
    "schema": "wslc-standard-caller-xvfb-r38-audit-v1",
    "attempt_id": pre["attempt_id"],
    "audited_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "classification": classification,
    "checks": checks,
    "counts": {"passed": sum(checks.values()), "total": len(checks)},
    "failed_checks": [name for name, passed in checks.items() if not passed],
    "observations": {
        "requested_pause_ms": 3600,
        "observed_pause_ms": pause["observed_pause_ms"],
        "cancel_response_ms": result["cancel_elapsed_ms"],
        "transaction_elapsed_ms": tx_ms,
        "release_deadline_margin_ms": margin_ms,
        "independent_release_readback_ms_after_cancel_start": parent_ms,
        "late_horizon_ms": horizon["ms_after_cancel_start"],
        "old_task": "pass",
        "fresh_task": "pass",
        "fresh_input_invocation_to_effect_readback_completed_ms": fresh_latency,
        "runtime_cleanup_status": result["cancel"]["cleanup_status"],
        "runtime_task_success": result["cancel"]["task_success"],
        "container_removed": checks["docker_container_removed"],
    },
    "limitations": [
        "single synthetic Xvfb container run",
        "not Windows desktop, MAP01, or a real application",
        "runtime cancellation remains UNKNOWN and replay denied",
        "one result is not a reliability or efficiency estimate",
    ],
    "raw_files": raw,
}
(root / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
lines = [f"classification={classification}", f"checks={sum(checks.values())}/{len(checks)}"]
lines.extend(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in checks.items())
(root / "AUDIT-EXECUTION.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
outcome = {
    "attempt_id": pre["attempt_id"],
    "classification": classification,
    "audit_passed": sum(checks.values()),
    "audit_total": len(checks),
    "retries": 0,
    "test_exit_code": 0,
    "docker_container_removed": checks["docker_container_removed"],
}
(root / "OUTCOME.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
result_md = f'''# R38 — WSLc 3.6 s private-Xvfb pause under a 4 s transaction deadline

**Disposition: `{classification}` ({sum(checks.values())}/{len(checks)} audit checks).** The unchanged public standard-caller test ran once in a digest-pinned Ubuntu container through Docker Desktop on the user-authorized PC. Networking was disabled; the container had 2 CPUs, 2 GiB memory, a 128 PID limit, an executable private 512 MiB `/tmp`, read-only repo/dependency/stage/XKB mounts, and a writable output mount. The exact container and Xvfb process were removed after the run.

Xvfb was paused for {pause['observed_pause_ms']:.3f} ms and resumed through its retained pidfd. The public cancel call returned in {result['cancel_elapsed_ms']:.3f} ms. Supervisor release/readback completed {tx_ms:.3f} ms after transaction admission, leaving {margin_ms:.3f} ms before the exact 4,000 ms deadline. Independent parent readback saw all keys up at +{parent_ms:.3f} ms. The +{horizon['ms_after_cancel_start']:.3f} ms horizon found all keys up and no delayed `b` press.

Old and fresh synthetic task oracles passed. The fresh effect count changed 0→1 and stayed 1 at the horizon; input invocation to independent effect readback completed in {fresh_latency:.3f} ms. The old cancellation remained UNKNOWN and replay-denied. Runtime cancellation fields remain UNKNOWN, `release_confirmed=false`, `replay_allowed=false`, and `task_success=null`.

## Scope

This is one synthetic-Xvfb sample at a 3,600 ms pause, 100 ms longer than R37. Its {margin_ms:.3f} ms release margin is narrow and does not establish a general safety margin. It does not establish Windows desktop, MAP01, real-application transfer, broad reliability, or matched efficiency. See the preregistration, raw output and {sum(checks.values())}-check audit in this directory. The initial audit attempt is retained; it had a false negative because it expected Docker's absent-object error to say `no such object` instead of the observed `no such container`.
'''
(root / "RESULT.md").write_text(result_md, encoding="utf-8")
print(f"{classification} {sum(checks.values())}/{len(checks)} release_margin_ms={margin_ms:.3f}")
if not all(checks.values()):
    raise SystemExit("R38 audit failed; outcome preserved")
