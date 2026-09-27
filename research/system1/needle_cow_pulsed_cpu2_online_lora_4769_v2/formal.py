"""Single host orchestration for the frozen 4769 Docker allocation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time

IMAGE = "needle-pilot05:local"
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
SEEDS = (91004321, 91004531, 91004749)
ARMS = (("CPU2_CONTINUOUS", 2), ("CPU2_PULSED", 2))
PREFIX = "research/system1/needle_cow_pulsed_cpu2_online_lora_4769_v2/"
ALLOCATION = "needle-cow-pulsed-cpu2-online-lora-4769-v2-20260928"
BRANCH = "research/needle-cow-pulsed-cpu2-online-lora-4769-v2-20260928"
LIMITS = ["--pull=never", "--platform=linux/amd64", "--network=none",
          "--read-only", "--memory=2g", "--pids-limit=64",
          "--security-opt=no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=64m"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def docker_path(path):
    return Path(path).resolve().as_posix()


def trainer_argv(source, out, seed, arm, cpus):
    return ["docker", "run", "--rm", *LIMITS, "--cpus", str(cpus),
            "--env", f"NEEDLE_EXPECTED_CPUS={cpus}",
            "--mount", f"type=bind,source={docker_path(source)},target=/src,readonly",
            "--mount", f"type=bind,source={docker_path(out)},target=/out",
            "--workdir", "/src", "--entrypoint", "/usr/local/bin/python", IMAGE,
            "-B", "/src/runner.py", "--seed", str(seed), "--arm", arm, "--out", "/out"]


def auditor_argv(source, raw, out):
    return ["docker", "run", "--rm", *LIMITS, "--cpus", "2",
            "--mount", f"type=bind,source={docker_path(source)},target=/src,readonly",
            "--mount", f"type=bind,source={docker_path(raw)},target=/raw,readonly",
            "--mount", f"type=bind,source={docker_path(out)},target=/out",
            "--workdir", "/src", "--entrypoint", "/usr/local/bin/python", IMAGE,
            "-B", "/src/audit.py", "--raw", "/raw", "--out", "/out/AUDIT.json"]


def verify_freeze(source):
    freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
    if tuple(freeze.get("formal_seeds", ())) != SEEDS:
        raise SystemExit("STOP_FREEZE_SEED_SET")
    if freeze.get("image_id") != IMAGE_ID or freeze.get("branch") != BRANCH:
        raise SystemExit("STOP_FREEZE_IDENTITY")
    github = freeze.get("github_readback", {})
    if not github.get("verified") or len(github.get("main_sha", "")) != 40:
        raise SystemExit("STOP_GITHUB_READBACK_IDENTITY")
    if len(github.get("issue_body_sha256", "")) != 64:
        raise SystemExit("STOP_GITHUB_ISSUE_HASH")
    source_hashes = freeze.get("source_sha256", {})
    if not source_hashes:
        raise SystemExit("STOP_SOURCE_HASHES_EMPTY")
    expected_paths = {PREFIX + path for path in source_hashes}
    records = {row.get("path"): row for row in github.get("files", [])}
    if set(records) != expected_paths:
        raise SystemExit("STOP_GITHUB_SOURCE_FILE_SET")
    for name, expected in source_hashes.items():
        if sha(source / name) != expected:
            raise SystemExit(f"STOP_SOURCE_HASH:{name}")
        rec = records[PREFIX + name]
        if rec.get("sha256") != expected or len(rec.get("blob_sha", "")) != 40:
            raise SystemExit(f"STOP_GITHUB_SOURCE_READBACK:{name}")
    collision = freeze.get("collision_audit", {})
    if collision.get("formal_seeds") != list(SEEDS):
        raise SystemExit("STOP_COLLISION_SEED_SET")
    if any(collision.get(k) != [] for k in ("issue_hits_other", "pr_hits", "branch_hits", "commit_hits")):
        raise SystemExit("STOP_SEED_COLLISION_HITS")
    if collision.get("main_code_hits") != {str(seed): 0 for seed in SEEDS}:
        raise SystemExit("STOP_MAIN_CODE_COLLISION")
    return freeze


def invoke(name, argv, out_root):
    start = time.time_ns()
    proc = subprocess.run(argv, capture_output=True)
    finish = time.time_ns()
    logdir = Path(out_root) / "logs"
    logdir.mkdir(parents=True, exist_ok=True)
    (logdir / f"{name}.stdout.bin").write_bytes(proc.stdout)
    (logdir / f"{name}.stderr.bin").write_bytes(proc.stderr)
    return {"name": name, "argv": argv, "exit_code": proc.returncode,
            "started_ns": start, "finished_ns": finish,
            "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest()}


def run(source, out):
    source, out = Path(source).resolve(), Path(out).resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise SystemExit("STOP_FORMAL_OUTPUT_NOT_EMPTY")
    if (out / "FORMAL_STARTED.json").exists():
        raise SystemExit("STOP_FORMAL_ALREADY_STARTED_NO_RETRY")
    freeze = verify_freeze(source)
    out.mkdir(parents=True, exist_ok=True)
    rawroot = out / "raw"
    rawroot.mkdir()
    image = subprocess.run(["docker", "image", "inspect", IMAGE, "--format",
                            "{{.Id}} {{.Os}}/{{.Architecture}}"], capture_output=True, text=True)
    if image.returncode or image.stdout.strip() != f"{IMAGE_ID} linux/amd64":
        raise SystemExit("STOP_IMAGE_ID_OR_PLATFORM")
    marker = {"allocation": freeze["allocation"], "started_ns": time.time_ns(),
              "seeds": list(SEEDS), "image": image.stdout.strip(),
              "branch": freeze["branch"], "main_sha": freeze["github_readback"]["main_sha"]}
    (out / "FORMAL_STARTED.json").write_text(json.dumps(marker, sort_keys=True) + "\n", encoding="utf-8")
    invocations = []
    order_by_seed = {}
    for index, seed in enumerate(SEEDS):
        ordered_arms = ARMS if index % 2 == 0 else tuple(reversed(ARMS))
        order_by_seed[str(seed)] = [arm for arm, _ in ordered_arms]
        for arm, cpus in ordered_arms:
            cell_out = rawroot / f"seed-{seed}" / arm.lower()
            cell_out.mkdir(parents=True)
            receipt = invoke(f"seed-{seed}-{arm.lower()}-trainer",
                             trainer_argv(source, cell_out, seed, arm, cpus), out)
            receipt.update({"seed": seed, "arm": arm, "cpu_quota": cpus})
            invocations.append(receipt)
    audit_out = out / "audit"
    audit_out.mkdir()
    audit_receipt = invoke("independent-auditor", auditor_argv(source, rawroot, audit_out), out)
    invocations.append(audit_receipt)
    audit_path = audit_out / "AUDIT.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else None
    final = {"allocation": freeze["allocation"], "formal_orchestrations": 1,
             "image": image.stdout.strip(), "host_platform": platform.platform(),
             "arm_order_by_seed": order_by_seed, "invocations": invocations,
             "completed_invocations": sum(x["exit_code"] == 0 for x in invocations),
             "audit_decision": audit.get("decision") if audit else None,
             "audit_errors": len(audit.get("errors", [])) if audit else None,
             "finished_ns": time.time_ns()}
    (out / "FORMAL_INVOCATION.json").write_text(json.dumps(final, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": freeze["allocation"], "invocations": len(invocations),
                      "failures": sum(x["exit_code"] != 0 for x in invocations),
                      "audit_decision": final["audit_decision"],
                      "audit_errors": final["audit_errors"]}, sort_keys=True), flush=True)
    if any(x["exit_code"] != 0 for x in invocations):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(args.source, args.out)
