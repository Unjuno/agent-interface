"""Fail-closed single-run OrbStack launcher and separate raw-only audit launcher."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

EXP_REL = Path("research/system1/needle_orbstack_publication_boundary_5134_20260930_01")
EXP = Path(__file__).resolve().parent
REPO = EXP.parents[2]
CONTEXT = "orbstack"
IMAGE = "sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
ALLOCATION = "needle-publication-orbstack-boundary-20260930-01"
OUT = Path("/tmp/unjuno-5134-orbstack-boundary-20260930-01")
MAIN = "c45e1947e498dce08abfb27e459e610054a0602e"
CONTAINER = "unjuno5134-boundary-pilot-20260930-01"
AUDITOR = "unjuno5134-boundary-audit-20260930-01"
SOURCE_NAMES = ("PLAN.md", "run.py", "audit.py", "launch.py", "test_pilot.py")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, text=True, capture_output=True, check=False)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def docker_argv(name: str, source: Path, writable: Path, env: dict[str, str],
                entry: str) -> list[str]:
    argv = ["docker", "--context", CONTEXT, "run", "--name", name,
            "--label", "unjuno.issue=5134", "--label", f"unjuno.allocation={ALLOCATION}",
            "--label", "unjuno.obstac.class=construction", "--platform", "linux/arm64",
            "--pull=never", "--network", "none", "--read-only", "--cpus", "0.25",
            "--memory", "512m", "--pids-limit", "32", "--shm-size", "32m",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--mount", f"type=bind,source={source},target=/src,readonly",
            "--mount", f"type=bind,source={writable},target=/out"]
    for key, value in env.items():
        argv += ["--env", f"{key}={value}"]
    argv += [IMAGE, "python", "-B", entry]
    return argv


def inspect(name: str) -> dict:
    result = run(["docker", "--context", CONTEXT, "inspect", name])
    if result.returncode:
        raise RuntimeError(f"inspect {name} failed: {result.stderr}")
    return json.loads(result.stdout)[0]


def check_mounts(container: dict, wanted: dict[str, tuple[str, bool]]) -> list[str]:
    actual = {m.get("Destination"): m for m in container.get("Mounts", [])}
    errors = []
    if set(actual) != set(wanted):
        errors.append("mount_destinations")
    for dest, (source, rw) in wanted.items():
        mount = actual.get(dest, {})
        if Path(mount.get("Source", "/missing")).resolve() != Path(source).resolve() or mount.get("RW") is not rw:
            errors.append("mount_" + dest)
    if container.get("Image") != IMAGE:
        errors.append("image_id")
    if container.get("Config", {}).get("Image") != IMAGE:
        errors.append("config_image")
    return errors


def gate() -> dict:
    if OUT.exists():
        raise RuntimeError("frozen pilot output already exists; never reuse/retry")
    if git("status", "--porcelain"):
        raise RuntimeError("frozen source checkout is not clean")
    commit, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    if git("merge-base", commit, MAIN) != MAIN:
        raise RuntimeError("source does not include frozen base main")
    fetched = run(["git", "fetch", "origin", "main"])
    if fetched.returncode:
        raise RuntimeError("cannot refresh origin/main: " + fetched.stderr.strip())
    live_main = git("rev-parse", "refs/remotes/origin/main")
    if git("merge-base", MAIN, live_main) != MAIN:
        raise RuntimeError("live main is not a descendant of frozen base main")
    seed_rel = "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json"
    if run(["git", "diff", "--quiet", MAIN, live_main, "--", seed_rel]).returncode != 0:
        raise RuntimeError("live main changed the frozen seed after base main")
    if run(["git", "diff", "--quiet", MAIN, live_main, "--", EXP_REL.as_posix()]).returncode != 0:
        raise RuntimeError("live main changed the pilot path after base main")
    freeze = json.loads((EXP / "FREEZE.json").read_text())
    if freeze.get("base_main_sha") != MAIN:
        raise RuntimeError("freeze/base-main mismatch")
    actual_hashes = {n: sha((EXP / n).read_bytes()) for n in SOURCE_NAMES}
    if actual_hashes != freeze.get("source_sha256"):
        raise RuntimeError("frozen source file hashes differ")
    seed = REPO / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json"
    if sha(seed.read_bytes()) != freeze.get("seed", {}).get("sha256"):
        raise RuntimeError("frozen seed hash differs")
    if git("rev-parse", "HEAD:" + str(seed.relative_to(REPO))) != freeze.get("seed", {}).get("git_blob"):
        raise RuntimeError("frozen seed Git blob differs")
    context = run(["docker", "--context", CONTEXT, "context", "show"])
    if context.returncode or context.stdout.strip() != CONTEXT:
        raise RuntimeError("OrbStack Docker context unavailable")
    image = run(["docker", "--context", CONTEXT, "image", "inspect", IMAGE,
                 "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"])
    if image.returncode or image.stdout.strip() != IMAGE + " linux/arm64":
        raise RuntimeError("pinned image/platform unavailable")
    for name in (CONTAINER, AUDITOR):
        check = run(["docker", "--context", CONTEXT, "inspect", name])
        if check.returncode == 0:
            raise RuntimeError("frozen container name already exists: " + name)
    inventory = run(["docker", "--context", CONTEXT, "ps", "--quiet"])
    if inventory.returncode or inventory.stdout.strip():
        raise RuntimeError("shared OrbStack inventory is occupied or unobservable")
    return {"source_commit": commit, "source_tree_sha": tree,
            "live_main_sha": live_main, "freeze_base_main_sha": MAIN,
            "freeze_sha256": sha((EXP / "FREEZE.json").read_bytes()),
            "source_sha256": actual_hashes, "image_id": IMAGE,
            "image_platform": "linux/arm64", "context": CONTEXT,
            "inventory_before_launch": inventory.stdout.strip(), "seed_sha256": sha(seed.read_bytes())}


def launch_one(argv: list[str], name: str, writable: Path, source: Path,
               input_mount: Path | None = None) -> tuple[int, dict, str, str]:
    # A new inventory snapshot immediately precedes each container invocation.
    inventory = run(["docker", "--context", CONTEXT, "ps", "--quiet"])
    if inventory.returncode or inventory.stdout.strip():
        raise RuntimeError("shared OrbStack lane changed before " + name)
    started = time.time_ns()
    proc = run(argv)
    ended = time.time_ns()
    stdout_path = writable / ("container.stdout.txt" if name == CONTAINER else "auditor.stdout.txt")
    stderr_path = writable / ("container.stderr.txt" if name == CONTAINER else "auditor.stderr.txt")
    stdout_path.write_text(proc.stdout); stderr_path.write_text(proc.stderr)
    container = inspect(name)
    wanted = {"/src": (str(source), False), "/out": (str(writable), True)}
    if input_mount is not None:
        wanted = {"/src": (str(source), False), "/in": (str(input_mount), False),
                  "/out": (str(writable), True)}
    errors = check_mounts(container, wanted)
    record = {"name": name, "argv": argv, "started_ns": started, "ended_ns": ended,
              "returncode": proc.returncode, "container_id": container.get("Id"),
              "state": container.get("State"), "mounts": container.get("Mounts"),
              "host_config": container.get("HostConfig"),
              "image": container.get("Image"), "config_image": container.get("Config", {}).get("Image"),
              "mount_errors": errors}
    return proc.returncode, record, proc.stdout, proc.stderr


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] != "--run-once":
        print("usage: launch.py --run-once", file=sys.stderr); return 2
    try:
        frozen = gate()
    except Exception as exc:
        print(json.dumps({"status": "STOP_BEFORE_OUTPUT_OR_DOCKER_RUN", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.mkdir()
    exp = EXP
    formal_env = {"OBSTAC_SOURCE_COMMIT": frozen["source_commit"], "OBSTAC_IMAGE_ID": IMAGE,
                  "OBSTAC_FREEZE_SHA256": frozen["freeze_sha256"], "OBSTAC_CONSTRUCTION": "1"}
    fargv = docker_argv(CONTAINER, REPO, OUT, formal_env,
                        "/src/" + EXP_REL.as_posix() + "/run.py")
    receipt = {"allocation": ALLOCATION, "issue": 5134, "construction": "1",
               "source_commit": frozen["source_commit"], "source_tree_sha": frozen["source_tree_sha"],
               "live_main_sha": frozen["live_main_sha"], "source_sha256": frozen["source_sha256"],
               "freeze_sha256": frozen["freeze_sha256"], "seed_sha256": frozen["seed_sha256"],
               "image_id": IMAGE, "platform": "linux/arm64", "docker_context": CONTEXT,
               "docker_version": run(["docker", "--context", CONTEXT, "version", "--format", "{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"]).stdout.strip(),
               "inventory_before_launch": frozen["inventory_before_launch"],
               "source_mount": str(REPO), "output_mount": str(OUT), "docker_argv": fargv,
               "formal_allocation_consumed": False,
               "scope": "one-transition OrbStack boundary pilot; not formal -03"}
    (OUT / "invocation_receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    exit_code, formal_record, _, _ = launch_one(fargv, CONTAINER, OUT, REPO)
    records = [formal_record]
    receipt["formal_container"] = formal_record
    (OUT / "invocation_receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    if exit_code == 0 and not formal_record["mount_errors"] and (OUT / "raw.json").is_file():
        audit_in, audit_out = OUT / "audit-input", OUT / "audit-output"
        audit_in.mkdir(); audit_out.mkdir()
        (audit_in / "raw.json").write_bytes((OUT / "raw.json").read_bytes())
        (audit_in / "invocation_receipt.json").write_bytes((OUT / "invocation_receipt.json").read_bytes())
        inputs = {n: sha((audit_in / n).read_bytes()) for n in ("raw.json", "invocation_receipt.json")}
        (audit_in / "input_manifest.json").write_text(json.dumps({"files": inputs}, sort_keys=True, indent=2) + "\n")
        audit_env = {**formal_env}
        aargv = docker_argv(AUDITOR, REPO, audit_out, audit_env,
                            "/src/" + EXP_REL.as_posix() + "/audit.py")
        # Insert isolated read-only audit input mount before env/image portion.
        marker = aargv.index("--env")
        aargv[marker:marker] = ["--mount", f"type=bind,source={audit_in},target=/in,readonly"]
        audit_exit, audit_record, _, _ = launch_one(aargv, AUDITOR, audit_out, REPO, audit_in)
        records.append(audit_record); exit_code = audit_exit
        receipt["auditor_container"] = audit_record
        (OUT / "invocation_receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    execution = {"allocation": ALLOCATION, "status": "EXECUTED",
                 "formal_container": records[0],
                 "audit_container": records[1] if len(records) > 1 else None,
                 "audit_output": str(OUT / "audit-output/audit.json") if len(records) > 1 else None,
                 "no_retry": True, "output": str(OUT)}
    (OUT / "execution.json").write_text(json.dumps(execution, sort_keys=True, indent=2) + "\n")
    print(json.dumps(execution, sort_keys=True))
    return 0 if exit_code == 0 and len(records) == 2 and not any(r["mount_errors"] for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
