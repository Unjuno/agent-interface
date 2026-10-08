"""One-shot host orchestrator for the frozen #4778 Docker allocation."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

ALLOCATION = "needle-intent-capacity-4679-v2"
BRANCH = "research/needle-intent-capacity-4679-v2-20260927"
PREFIX = "research/system1/needle_intent_capacity_4679_v2/"
IMAGE = "needle-pilot05:local"
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
SEEDS = (4153201, 4153203, 4153207)
SOURCE_FILES = (
    "runner.py", "audit.py", "test_construction.py", "PREREGISTRATION.md",
    "ISSUE_CONTRACT.md", "README.md", "formal.py",
)
LIMITS = [
    "--pull=never", "--platform", "linux/amd64", "--network", "none",
    "--read-only", "--cpus=1", "--memory=2g", "--pids-limit=64",
    "--security-opt=no-new-privileges", "--tmpfs",
    "/tmp:rw,nosuid,nodev,noexec,size=256m",
]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def docker_path(path):
    return Path(path).resolve().as_posix()


def inspect_image():
    proc = subprocess.run(
        ["docker", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"],
        capture_output=True, text=True,
    )
    return {"exit_code": proc.returncode, "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.decode(errors="replace") if isinstance(proc.stderr, bytes) else proc.stderr.strip()}


def verify_freeze(source):
    freeze_bytes = (source / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes.decode("utf-8"))
    if freeze.get("allocation") != ALLOCATION or freeze.get("branch") != BRANCH:
        raise SystemExit("STOP_FREEZE_ALLOCATION_OR_BRANCH")
    if tuple(freeze.get("formal_seeds", ())) != SEEDS:
        raise SystemExit("STOP_FREEZE_SEEDS")
    if freeze.get("image_id") != IMAGE_ID or freeze.get("platform") != "linux/amd64":
        raise SystemExit("STOP_FREEZE_IMAGE_ID")
    readback = freeze.get("github_readback", {})
    if (readback.get("verified") is not True or len(readback.get("main_sha", "")) != 40
            or len(readback.get("issue_body_sha256", "")) != 64):
        raise SystemExit("STOP_FREEZE_GITHUB_READBACK")
    source_hashes = freeze.get("source_sha256", {})
    if set(source_hashes) != set(SOURCE_FILES):
        raise SystemExit("STOP_FREEZE_SOURCE_SET")
    expected_remote_paths = {PREFIX + name for name in SOURCE_FILES}
    records = {row.get("path"): row for row in readback.get("files", [])}
    if set(records) != expected_remote_paths:
        raise SystemExit("STOP_GITHUB_READBACK_SOURCE_SET")
    for name in SOURCE_FILES:
        local_hash = sha256((source / name).read_bytes())
        if local_hash != source_hashes[name]:
            raise SystemExit(f"STOP_LOCAL_SOURCE_HASH:{name}")
        remote = records[PREFIX + name]
        if (remote.get("sha256") != local_hash or len(remote.get("blob_sha", "")) != 40):
            raise SystemExit(f"STOP_REMOTE_SOURCE_IDENTITY:{name}")
    collision = freeze.get("collision_audit", {})
    if collision.get("formal_seeds") != list(SEEDS):
        raise SystemExit("STOP_COLLISION_SEEDS")
    for key in ("issue_hits_other", "pr_hits", "branch_hits", "commit_hits", "main_code_exact_hits"):
        if collision.get(key) != []:
            raise SystemExit(f"STOP_COLLISION:{key}")
    if freeze.get("formal_runs_at_freeze") != 0:
        raise SystemExit("STOP_FORMAL_ALREADY_CONSUMED")
    return freeze, freeze_bytes


def trainer_argv(source, raw):
    return ["docker", "run", "--rm", *LIMITS,
            "--mount", f"type=bind,source={docker_path(source)},target=/src,readonly",
            "--mount", f"type=bind,source={docker_path(raw)},target=/out",
            "--workdir", "/src", "--entrypoint", "/usr/local/bin/python", IMAGE,
            "-B", "/src/runner.py", "--formal", "--out", "/out"]


def auditor_argv(source, raw, audit_dir):
    return ["docker", "run", "--rm", *LIMITS,
            "--mount", f"type=bind,source={docker_path(source)},target=/src,readonly",
            "--mount", f"type=bind,source={docker_path(raw)},target=/raw,readonly",
            "--mount", f"type=bind,source={docker_path(audit_dir)},target=/out",
            "--workdir", "/src", "--entrypoint", "/usr/local/bin/python", IMAGE,
            "-B", "/src/audit.py", "--raw", "/raw", "--out", "/out/AUDIT.json"]


def invoke(name, argv, out):
    started = time.time_ns()
    proc = subprocess.run(argv, capture_output=True)
    finished = time.time_ns()
    logs = Path(out) / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    stdout_path = logs / f"{name}.stdout.bin"
    stderr_path = logs / f"{name}.stderr.bin"
    stdout_path.write_bytes(proc.stdout)
    stderr_path.write_bytes(proc.stderr)
    return {"name": name, "argv": argv, "started_ns": started, "finished_ns": finished,
            "exit_code": proc.returncode, "stdout_sha256": sha256(proc.stdout),
            "stderr_sha256": sha256(proc.stderr),
            "stdout_path": stdout_path.relative_to(out).as_posix(),
            "stderr_path": stderr_path.relative_to(out).as_posix()}


def run(source, out):
    source, out = Path(source).resolve(), Path(out).resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS_OR_NONEMPTY")
    freeze, freeze_bytes = verify_freeze(source)
    before = inspect_image()
    if before["exit_code"] or before["stdout"] != f"{IMAGE_ID} linux/amd64":
        raise SystemExit("STOP_LOCAL_IMAGE_ID_OR_PLATFORM")
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "raw"
    audit_dir = out / "audit"
    raw.mkdir()
    audit_dir.mkdir()
    marker = {"allocation": ALLOCATION, "started_ns": time.time_ns(),
              "formal_orchestrations": 1, "formal_seeds": list(SEEDS),
              "freeze_sha256": sha256(freeze_bytes), "branch": BRANCH,
              "main_sha_at_freeze": freeze["github_readback"]["main_sha"],
              "image_before": before}
    (out / "FORMAL_STARTED.json").write_text(
        json.dumps(marker, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    trainer = invoke("trainer", trainer_argv(source, raw), out)
    auditor = invoke("independent-auditor", auditor_argv(source, raw, audit_dir), out)
    after = inspect_image()
    audit_path = audit_dir / "AUDIT.json"
    audit_report = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else None
    invocation = {
        "schema": "needle-intent-capacity.invocation.v1", "allocation": ALLOCATION,
        "formal_orchestrations": 1, "host_platform": platform.platform(),
        "host_python": platform.python_version(), "image_before": before,
        "image_after": after, "trainer": trainer, "auditor": auditor,
        "audit_decision": audit_report.get("decision") if audit_report else None,
        "audit_errors": len(audit_report.get("errors", [])) if audit_report else None,
        "finished_ns": time.time_ns(),
    }
    (out / "FORMAL_INVOCATION.json").write_text(
        json.dumps(invocation, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": ALLOCATION, "trainer_exit": trainer["exit_code"],
                      "auditor_exit": auditor["exit_code"],
                      "audit_decision": invocation["audit_decision"],
                      "audit_errors": invocation["audit_errors"]}, sort_keys=True), flush=True)
    if trainer["exit_code"] or auditor["exit_code"] or not audit_report:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(args.source, args.out)
