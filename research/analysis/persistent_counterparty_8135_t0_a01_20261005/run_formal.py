#!/usr/bin/env python3
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
IMAGE = "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def common():
    return ["docker", "run", "--pull=never", "--rm", "--network=none", "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--cpus=1", "--memory=1g"]


def ro(src, dst):
    return ["--mount", f"type=bind,src={src},dst={dst},readonly"]


def rw(src, dst):
    return ["--mount", f"type=bind,src={src},dst={dst}"]


def invoke(cmd, out, err):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        out.write_text(p.stdout); err.write_text(p.stderr)
        return p.returncode
    except subprocess.TimeoutExpired as e:
        out.write_text(e.stdout or ""); err.write_text(e.stderr or "")
        return 124


def main():
    frozen = json.loads((ROOT/"FROZEN.json").read_text())
    subprocess.check_call(["git", "fetch", "origin", "main"], cwd=ROOT)
    latest = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip()
    base = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    if latest != frozen["base_commit"] or base != frozen["base_commit"]:
        raise SystemExit(f"STOP_MAIN_CHANGED frozen={frozen['base_commit']} latest={latest} merge_base={base}")
    for name, digest in frozen["source_sha256"].items():
        if sha(ROOT/name) != digest:
            raise SystemExit("STOP_FROZEN_SOURCE_CHANGED:"+name)
    if sha(ROOT/"bundle/manifest.json") != frozen["manifest_sha256"] or sha(ROOT/"bundle/sealed_truth.json") != frozen["truth_sha256"]:
        raise SystemExit("STOP_FROZEN_INPUT_CHANGED")
    image_id = subprocess.check_output(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"], text=True).strip()
    if image_id != frozen["image_id"]:
        raise SystemExit("STOP_IMAGE_IDENTITY:"+image_id)
    results = ROOT/"results"
    if results.exists() and any(p.is_file() for p in results.rglob("*")):
        raise SystemExit("STOP_RESULTS_NOT_EMPTY")
    co, ao = results/"candidate-out", results/"audit-out"
    co.mkdir(parents=True, exist_ok=True); ao.mkdir(parents=True, exist_ok=True)
    cp = co/"candidate.json"
    candidate_cmd = common()+ro(ROOT/"candidate.py", "/src/candidate.py")+ro(ROOT/"bundle/manifest.json", "/input/manifest.json")+rw(co, "/output")+["-w", "/work", IMAGE, "python", "-B", "/src/candidate.py", "/input/manifest.json", "/output/candidate.json"]
    record = {"allocation": frozen["allocation"], "started_at_utc": datetime.now(timezone.utc).isoformat(), "candidate_invocations": 1, "auditor_invocations": 0, "retries": 0, "candidate_command": candidate_cmd, "auditor_command": None, "candidate_exit": None, "auditor_exit": None, "state": "CANDIDATE_RUNNING"}
    (ROOT/"FORMAL_STARTED.json").write_text(json.dumps(record, sort_keys=True, indent=2)+"\n")
    rc = invoke(candidate_cmd, results/"candidate.stdout.txt", results/"candidate.stderr.txt")
    record["candidate_exit"] = rc
    if rc or not cp.exists():
        record["state"] = "STOP_CANDIDATE_FAILED"; (ROOT/"RUN_RECORD.json").write_text(json.dumps(record, sort_keys=True, indent=2)+"\n"); raise SystemExit(record["state"])
    audit_path = ao/"audit.json"
    audit_cmd = common()+ro(ROOT/"audit.py", "/src/audit.py")+ro(ROOT/"bundle/manifest.json", "/input/manifest.json")+ro(ROOT/"bundle/sealed_truth.json", "/input/sealed_truth.json")+ro(cp, "/candidate/candidate.json")+rw(ao, "/output")+["-w", "/work", IMAGE, "python", "-B", "/src/audit.py", "/input/manifest.json", "/input/sealed_truth.json", "/candidate/candidate.json", "/output/audit.json"]
    record.update({"auditor_invocations": 1, "auditor_command": audit_cmd, "state": "AUDITOR_RUNNING"})
    (ROOT/"FORMAL_STARTED.json").write_text(json.dumps(record, sort_keys=True, indent=2)+"\n")
    rc = invoke(audit_cmd, results/"auditor.stdout.txt", results/"auditor.stderr.txt")
    record.update({"auditor_exit": rc, "candidate_sha256": sha(cp), "audit_sha256": sha(audit_path) if audit_path.exists() else None, "state": "COMPLETE" if rc == 0 else "FAIL_OR_STOP_AUDITOR"})
    for name in ("FORMAL_STARTED.json", "RUN_RECORD.json"):
        (ROOT/name).write_text(json.dumps(record, sort_keys=True, indent=2)+"\n")
    if rc:
        raise SystemExit(record["state"])


if __name__ == "__main__":
    main()
