import datetime, hashlib, json, subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
repo = root.parents[2]
out = root / "output"
load = lambda p: json.loads((root / p).read_text(encoding="utf-8-sig"))
pre, cond, inv = load("PREREGISTRATION.json"), load("CONDITIONS.json"), load("INVOCATION-METADATA.json")
r = load("output/result.json")
checks = {}
def check(k, v): checks[k] = bool(v)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

check("attempt_pins", pre["attempt_id"] == cond["attempt_id"] == inv["attempt_id"] == "wslc-standard-caller-xvfb-20261025-r42" and pre["source_commit"] == cond["source_commit"])
for rel, digest in pre["source_hashes"].items():
    check("raw_sha_" + rel.replace("/", "_"), sha(repo/rel) == digest)
    tree = subprocess.run(["git", "rev-parse", f'{pre["source_commit"]}:{rel}'], cwd=repo, capture_output=True, text=True)
    work = subprocess.run(["git", "hash-object", "--path="+rel, rel], cwd=repo, capture_output=True, text=True)
    check("commit_blob_" + rel.replace("/", "_"), tree.returncode == work.returncode == 0 and tree.stdout.strip() == work.stdout.strip())

state = (out/"container-state-before-cleanup.txt").read_text()
mounts = (out/"container-mounts-before-cleanup.txt").read_text().splitlines()
check("image_digest", pre["image"] in (out/"pinned-image-inspect.txt").read_text() and pre["image"] in state)
check("network_and_limits", " none " in state and "2147483648" in state and "2000000000" in state and "128" in state)
check("readonly_mounts", all(f"{p}:readonly=true" in mounts for p in ["/repo", "/deps", "/stage", "/xkb"]) and "/out:readonly=false" in mounts)
check("exec_tmpfs", "rw,exec,nosuid,nodev,mode=1777,size=512m" in state)
stderr = (out/"runner.stderr.txt").read_text()
check("xres_preflight_before_input", (out/"preflight-status.txt").read_text().strip() == "pass" and "local_xres_identity=" in (out/"xvfb-process-identity-preflight.txt").read_text() and (out/"trial-started.txt").exists())
check("expected_public_assertion_failure", (out/"docker-run-exit-code.txt").read_text().strip() == "1" and (out/"test-exit-code.txt").read_text().strip() == "1" and "FAILED (failures=1)" in stderr and "transaction_deadline" in stderr and "AssertionError: 'unknown' != 'disconnected'" in stderr)
pause = r["xvfb_server_pause"]
check("3900ms_pidfd_pause", pause["requested_pause_ms"] == 3900 and pause["observed_pause_ms"] >= 3900 and pause["signal_identity"] == "retained_pidfd" and pause["resume_receipt"]["error"] is None)
tx = r["cancel"]["cancellation"]
start, deadline, completed = tx["admitted_monotonic_ns"], tx["transaction_deadline_monotonic_ns"], tx["completed_monotonic_ns"]
late_ms = (completed-deadline)/1e6
check("exact_4s_deadline", deadline-start == 4_000_000_000)
check("completion_just_after_deadline", completed > deadline and 0 < late_ms < 100)
check("release_unknown_transaction_deadline", r["cancel"]["cleanup_status"] == "UNKNOWN" and r["cancel"]["owner_release_attempt"]["status"] == "unknown" and r["cancel"]["owner_release_attempt"]["reason"] == "transaction_deadline")
check("unknown_fence_replay_denied", r["cancel"]["release_confirmed"] is False and r["cancel"]["replay_allowed"] is False and r["cancel"]["task_success"] is None)
check("no_independent_readback_or_task_oracles", r["independent_release_readback"] is None and r.get("independent_task_oracle") is None and r.get("counted_task_outcomes") is None and r.get("fresh_session_recovery") is None)
check("xvfb_stopped", (out/"xvfb-process-absent-after-run.txt").read_text().strip().lower() == "true")
check("container_removed", (out/"docker-cleanup-exit-code.txt").read_text().strip() == "0" and (out/"container-inspect-after-cleanup-exit-code.txt").read_text().strip() != "0" and "no such container" in (out/"container-inspect-after-cleanup.txt").read_text().lower())
stage = json.loads((repo/"research/integration/wslc_standard_caller_xvfb_20261025_r33/STAGE-MANIFEST.json").read_text(encoding="utf-8-sig"))
stage_root = repo/"research/integration/wslc_standard_caller_xvfb_20261025_r16/stage"
check("staged_dependencies_hashes", len(stage) == 1252 and all(sha(stage_root/x["path"]) == x["sha256"] for x in stage))
xkb = json.loads((repo/"research/integration/wslc_standard_caller_xvfb_20261025_r34/xkb-materialization.json").read_text(encoding="utf-8-sig"))
xkb_root = repo/"research/integration/wslc_standard_caller_xvfb_20261025_r34/xkb-materialized"
check("xkb_hashes", xkb["files"] == 293 and all(sha(xkb_root/x["path"]) == x["sha256"] for x in xkb["manifest"]))
check("cancel_response_under_3s", r["cancel_elapsed_ms"] < 3000)

raw=[]
for p in sorted(root.rglob("*")):
    if p.is_file() and p.name not in {"AUDIT.json", "AUDIT-EXECUTION.log", "OUTCOME.json", "RESULT.md"}:
        raw.append({"path":p.relative_to(repo).as_posix(),"sha256":sha(p),"bytes":p.stat().st_size})
report={"schema":"wslc-r42-boundary-audit-v1","attempt_id":pre["attempt_id"],"audited_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"classification":"FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN","evidence_checks":checks,"evidence_counts":{"passed":sum(checks.values()),"total":len(checks)},"failed_evidence_checks":[k for k,v in checks.items() if not v],"observations":{"requested_pause_ms":3900,"observed_pause_ms":pause["observed_pause_ms"],"cancel_response_ms":r["cancel_elapsed_ms"],"transaction_elapsed_ms":(completed-start)/1e6,"transaction_overrun_ms":late_ms,"release_status":"UNKNOWN","independent_release_readback":None,"task_oracles":"not reached","replay_allowed":False,"runtime_task_success":None,"container_removed":checks["container_removed"]},"limitations":["one synthetic Xvfb boundary probe","no independent release readback or task oracle completed","runtime cancellation remains UNKNOWN and replay denied","not Windows desktop, MAP01, a real application, or a reliability estimate"],"raw_files":raw}
(root/"AUDIT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
lines=["classification=FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN",f"evidence_checks={sum(checks.values())}/{len(checks)}"]+[f"{k}={'PASS' if v else 'FAIL'}" for k,v in checks.items()]
(root/"AUDIT-EXECUTION.log").write_text("\n".join(lines)+"\n",encoding="utf-8")
outcome={"attempt_id":pre["attempt_id"],"classification":"FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN","evidence_checks_passed":sum(checks.values()),"evidence_checks_total":len(checks),"caller_test_exit_code":1,"release_status":"UNKNOWN","independent_release_readback":False,"task_oracles_reached":False,"retries":0,"container_removed":checks["container_removed"]}
(root/"OUTCOME.json").write_text(json.dumps(outcome,indent=2)+"\n",encoding="utf-8")
result_md=f'''# R42 — WSLc 3.9 s boundary probe under a 4 s transaction deadline

**Disposition: `FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN`.** The unchanged public standard-caller test failed once at its cancel assertion. Xvfb was paused for {pause['observed_pause_ms']:.3f} ms and resumed through its retained pidfd. The public cancel call returned in {r['cancel_elapsed_ms']:.3f} ms, but the cancellation transaction completed {(completed-start)/1e6:.3f} ms after admission, {late_ms:.3f} ms beyond its exact 4,000 ms deadline. The owner release worker and client disconnect status were `UNKNOWN` with reason `transaction_deadline`; `release_confirmed=false`, replay remained denied, and `task_success=null`.

The test stopped at that assertion. It produced no independent release readback, late-event horizon, old-task oracle, or fresh-generation task oracle. The exact Xvfb process and container were removed. Destroying the private synthetic X server is environment teardown, not an agent release receipt, so the runtime state remains UNKNOWN. Evidence-integrity checks: {sum(checks.values())}/{len(checks)}; raw output and the full caller assertion are retained here. No retry was made.

## Scope

R40 and R41 passed 3,800 ms holds with 76.372 and 72.300 ms release margins. R42 at 3,900 ms exceeded its transaction deadline by {late_ms:.3f} ms and the public caller test failed. This single synthetic-Xvfb result bounds the tested 4 s transaction for this host/runtime; it is not a general reliability estimate and does not establish Windows desktop, MAP01, real-app transfer, or matched efficiency.
'''
(root/"RESULT.md").write_text(result_md,encoding="utf-8")
print(f"FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN evidence_checks={sum(checks.values())}/{len(checks)} overrun_ms={late_ms:.3f}")
if not all(checks.values()): raise SystemExit("R42 evidence integrity check failed")
