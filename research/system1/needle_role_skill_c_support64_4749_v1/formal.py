"""One-shot host orchestrator for Issue #4749; every trainer/loader runs in Docker."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time

SEEDS = (7865101, 7865201, 7865301, 7865401, 7865501,
         7865601, 7865701, 7865801, 7865901, 7866001)
ARMS = ("control16", "treatment64")
IMAGE = "needle-pilot05:local"
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
LIMITS = ["--pull=never", "--platform", "linux/amd64", "--network", "none", "--read-only", "--cpus=1",
          "--memory=2g", "--pids-limit=64", "--security-opt=no-new-privileges",
          "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def docker_path(path):
    return Path(path).resolve().as_posix()


def builder_argv(source, out, seed):
    return ["docker", "run", "--rm", *LIMITS,
            "--env", f"NEEDLE_SEED={seed}", "--env", "NEEDLE_OUTPUT=/out",
            "--mount", f"type=bind,source={docker_path(source)},target=/src,readonly",
            "--mount", f"type=bind,source={docker_path(out)},target=/out",
            "--workdir", "/src", "--entrypoint", "/usr/local/bin/python", IMAGE,
            "-B", "/src/support_formal_builder.py"]


def loader_argv(source, package, out):
    return ["docker", "run", "--rm", *LIMITS,
            "--mount", f"type=bind,source={docker_path(source)},target=/src,readonly",
            "--mount", f"type=bind,source={docker_path(package)},target=/pkg,readonly",
            "--mount", f"type=bind,source={docker_path(out)},target=/load",
            "--workdir", "/src", "--entrypoint", "/usr/local/bin/python", IMAGE,
            "-B", "/src/support_loader.py", "/pkg/skill.json", "/pkg/expected.json",
            "/load/loader.json"]


def audit_argv(source, raw, baseline, out):
    return ["docker", "run", "--rm", *LIMITS,
            "--mount", f"type=bind,source={docker_path(source)},target=/src,readonly",
            "--mount", f"type=bind,source={docker_path(raw)},target=/raw,readonly",
            "--mount", f"type=bind,source={docker_path(baseline)},target=/baseline,readonly",
            "--mount", f"type=bind,source={docker_path(out)},target=/out",
            "--workdir", "/src", "--entrypoint", "/usr/local/bin/python", IMAGE,
            "-B", "/src/audit_formal.py", "--raw", "/raw", "--baseline", "/baseline/runner.py",
            "--out", "/out"]


def invoke(name, argv, root, receipt):
    started = time.time_ns()
    proc = subprocess.run(argv, capture_output=True)
    ended = time.time_ns()
    d = Path(root) / "logs"
    d.mkdir(exist_ok=True)
    (d / f"{name}.stdout.bin").write_bytes(proc.stdout)
    (d / f"{name}.stderr.bin").write_bytes(proc.stderr)
    receipt.append({"name": name, "argv": argv, "exit_code": proc.returncode,
                    "started_ns": started, "finished_ns": ended,
                    "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(),
                    "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest()})
    return proc.returncode


def run(source, root):
    source = Path(source).resolve()
    root = Path(root).resolve()
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise SystemExit("STOP_FORMAL_OUTPUT_NOT_EMPTY_OR_DIRECTORY")
    root.mkdir(parents=True, exist_ok=True)
    marker = root / "FORMAL_STARTED.json"
    if marker.exists():
        raise SystemExit("STOP_FORMAL_ALREADY_STARTED_NO_RETRY")
    freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
    if tuple(freeze["formal_seeds"]) != SEEDS or freeze["image_id"] != IMAGE_ID:
        raise SystemExit("STOP_FREEZE_IDENTITY")
    if not freeze.get("github_readback", {}).get("verified"):
        raise SystemExit("STOP_GITHUB_READBACK_NOT_VERIFIED")
    readback = freeze["github_readback"]
    if not readback.get("main_sha") or len(readback.get("main_sha", "")) != 40:
        raise SystemExit("STOP_GITHUB_READBACK_IDENTITY")
    if len(readback.get("issue_body_sha256", "")) != 64:
        raise SystemExit("STOP_GITHUB_ISSUE_HASH")
    entries = readback.get("files", [])
    if not entries:
        raise SystemExit("STOP_GITHUB_FILE_READBACK_MISSING")
    prefix = "research/system1/needle_role_skill_c_support64_4749_v1/"
    recorded = {item.get("path"): item for item in entries}
    expected_paths = {prefix + name for name in freeze["source_sha256"]}
    if set(recorded) != expected_paths:
        raise SystemExit("STOP_GITHUB_FILE_READBACK_SET")
    for name, expected in freeze["source_sha256"].items():
        item = recorded[prefix + name]
        if item.get("sha256") != expected or len(item.get("blob_sha", "")) != 40:
            raise SystemExit(f"STOP_GITHUB_FILE_READBACK_HASH:{name}")
    if not freeze.get("collision_audit", {}).get("verified"):
        raise SystemExit("STOP_COLLISION_AUDIT_NOT_VERIFIED")
    collision = freeze["collision_audit"]
    if tuple(collision.get("formal_seeds", ())) != SEEDS:
        raise SystemExit("STOP_COLLISION_SEED_SET")
    if any(collision.get(bucket) != [] for bucket in
           ("issue_hits_other", "pr_hits", "branch_hits", "commit_hits")):
        raise SystemExit("STOP_COLLISION_HITS")
    if collision.get("main_code_hits") != {str(seed): 0 for seed in SEEDS}:
        raise SystemExit("STOP_MAIN_CODE_COLLISIONS")
    for name, expected in freeze["source_sha256"].items():
        if sha(source / name) != expected:
            raise SystemExit(f"STOP_SOURCE_HASH:{name}")
    image = subprocess.run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"], capture_output=True, text=True)
    if image.returncode != 0 or image.stdout.strip() != f"{IMAGE_ID} linux/amd64":
        raise SystemExit("STOP_IMAGE_ID_OR_PLATFORM")
    marker.write_text(json.dumps({"allocation": freeze["allocation"], "started_ns": time.time_ns(),
                                  "seeds": list(SEEDS), "image": image.stdout.strip()}, sort_keys=True) + "\n", encoding="utf-8")
    receipt = []
    for seed in SEEDS:
        seed_root = root / f"seed-{seed}"
        builder_out = seed_root / "builder"
        builder_out.mkdir(parents=True)
        code = invoke(f"seed-{seed}-builder", builder_argv(source, builder_out, seed), root, receipt)
        if code != 0:
            continue
        packages_ok = all((builder_out / arm / name).is_file()
                          for arm in ARMS for name in ("skill.json", "expected.json"))
        if not packages_ok:
            receipt.append({"name": f"seed-{seed}-builder-output", "exit_code": 90})
            continue
        for arm in ARMS:
            package = builder_out / arm
            for loader in ("load1", "load2"):
                load_out = seed_root / arm / loader
                load_out.mkdir(parents=True)
                argv = loader_argv(source, package, load_out)
                before = sha(package / "skill.json")
                invoke(f"seed-{seed}-{arm}-{loader}", argv, root, receipt)
                after = sha(package / "skill.json")
                receipt[-1].update({"package_sha256_before": before, "package_sha256_after": after,
                                    "package_immutable": before == after})
                if before != after:
                    receipt[-1]["exit_code"] = 91
    audit_out = root / "audit"
    audit_out.mkdir()
    audit_exit = invoke("independent-auditor", audit_argv(source, root, source / "source", audit_out), root, receipt)
    final = {"allocation": freeze["allocation"], "formal_orchestrations": 1,
             "image": image.stdout.strip(), "host_platform": platform.platform(),
             "invocations": receipt, "audit_exit_code": audit_exit,
             "completed_invocations": sum(x.get("exit_code") == 0 for x in receipt),
             "finished_ns": time.time_ns()}
    (root / "FORMAL_INVOCATION.json").write_text(json.dumps(final, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": freeze["allocation"], "invocations": len(receipt),
                      "failures": sum(x.get("exit_code") != 0 for x in receipt),
                      "audit_exit_code": audit_exit}, sort_keys=True), flush=True)
    if any(x.get("exit_code") != 0 for x in receipt):
        raise SystemExit(1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    run(a.source, a.out)
