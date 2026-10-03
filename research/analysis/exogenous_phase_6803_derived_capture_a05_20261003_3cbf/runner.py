"""Host-side one-shot runtime controller; generated files are never overwritten."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
ORB = "/opt/homebrew/bin/orbctl"
VM = "research-6183-t0-20261003"
ALLOCATION = "PHASE-6803-A05-ORBSTACK-20261003-3CBF-01"
NAME = "phase-6969-a05-3cbf"
INPUT = "/home/taka/inputs/" + NAME
OUTPUT = "/home/taka/outputs/" + NAME
IMAGE = "python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016"
OLD = ROOT.parent / "exogenous_opportunity_5694_matched_phase_a04_20261002"


def dump(path, value):
    with path.open("x") as target:
        json.dump(value, target, sort_keys=True, indent=2)
        target.write("\n")


def remote(*args):
    return subprocess.run([ORB, "run", "-m", VM, *args], capture_output=True, text=True, check=True).stdout


def verify_sources():
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    for name, wanted in freeze["source_sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != wanted:
            raise ValueError("frozen source changed: " + name)
    for name, wanted in freeze["legacy_sha256"].items():
        if hashlib.sha256((OLD / name).read_bytes()).hexdigest() != wanted:
            raise ValueError("pinned legacy source changed: " + name)
    return freeze


def stage():
    freeze = verify_sources()
    # Only this thread's named VM and new paths are touched.
    remote("test", "!", "-e", INPUT)
    remote("test", "!", "-e", OUTPUT)
    containers = remote("docker", "ps", "-a", "--format", "{{.Names}}")
    if any(NAME in line for line in containers.splitlines()):
        raise ValueError("allocation container already exists")
    image = json.loads(remote("docker", "image", "inspect", IMAGE))
    if image[0]["Id"] != IMAGE.split("@", 1)[1] or image[0]["Architecture"] != "arm64":
        raise ValueError("cached image identity mismatch")
    paths = [INPUT + "-" + role for role in ("candidate", "legacy", "auditor")]
    for path in paths:
        remote("test", "!", "-e", path)
    remote("mkdir", "-p", *paths, OUTPUT + "/candidate", OUTPUT + "/legacy", OUTPUT + "/auditor")
    for role in ("candidate", "legacy", "auditor"):
        if remote("stat", "-c", "%u:%g", OUTPUT + "/" + role).strip() != "501:501":
            raise ValueError("output owner does not match frozen non-root UID")
        remote("test", "-w", OUTPUT + "/" + role)
    packages = {
        "candidate": [ROOT / "candidate.py", ROOT / "fixture.json"],
        "legacy": [ROOT / "legacy_probe.py", OLD / "candidate.py", OLD / "fixture.json"],
        "auditor": [ROOT / "audit.py", ROOT / "fixture.json"],
    }
    custody = {}
    for role, files in packages.items():
        destination = INPUT + "-" + role
        subprocess.run([ORB, "push", "-m", VM, *(str(p) for p in files), destination + "/"], check=True)
        observed = remote("sha256sum", *(destination + "/" + p.name for p in files))
        for p in files:
            if hashlib.sha256(p.read_bytes()).hexdigest() + "  " + destination + "/" + p.name not in observed.splitlines():
                raise ValueError("staged hash mismatch: " + str(p))
        listing = remote("find", destination, "-maxdepth", "1", "-type", "f", "-printf", "%f\n").splitlines()
        if sorted(listing) != sorted(p.name for p in files):
            raise ValueError("source mount has unexpected files")
        custody[role] = {"path": destination, "contains_only": sorted(listing), "sha256sum": observed}
    dump(ROOT / "STAGING.json", {"allocation": ALLOCATION, "image": image,
         "custody": custody, "docker_info": json.loads(remote("docker", "info", "--format", "{{json .}}")),
         "vm_cgroup": remote("sh", "-c", "cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/cpu.max"),
         "output_ownership": remote("stat", "-c", "%u:%g %a %n", OUTPUT + "/candidate", OUTPUT + "/legacy", OUTPUT + "/auditor"),
         "source_sha256": freeze["source_sha256"]})


def command(role):
    args = ["docker", "run", "--pull", "never", "--name", NAME + "-" + role,
            "--network", "none", "--cpus", "1", "--memory", "512m", "--read-only", "--user", "501:501",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m", "--mount",
            "type=bind,src=" + INPUT + "-" + role + ",dst=/src,readonly", "--mount",
            "type=bind,src=" + OUTPUT + "/" + role + ",dst=/out", "-e", "PYTHONDONTWRITEBYTECODE=1", "-w", "/src"]
    if role == "candidate":
        invocation = "python /src/candidate.py --fixture /src/fixture.json --out /out/raw.json"
    elif role == "legacy":
        invocation = "python /src/legacy_probe.py --source /src/candidate.py --fixture /src/fixture.json --out /out/probe.json"
    else:
        for origin, destination in (("candidate", "/candidate"), ("legacy", "/legacy")):
            args += ["--mount", "type=bind,src=" + OUTPUT + "/" + origin + ",dst=" + destination + ",readonly"]
        invocation = "python /src/audit.py --fixture /src/fixture.json --raw /candidate/raw.json --legacy /legacy/probe.json --out /out/audit.json --mutations-out /out/mutations.json"
    shell = "set -eu; cat /sys/fs/cgroup/memory.max > /out/memory.max; cat /sys/fs/cgroup/cpu.max > /out/cpu.max; " + invocation + " > /out/stdout.log 2> /out/stderr.log"
    return args + [IMAGE, "sh", "-c", shell]


def execute(source_commit):
    verify_sources()
    current_commit = subprocess.run(["/Library/Developer/CommandLineTools/usr/bin/git", "rev-parse", "HEAD"],
                                    cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if current_commit != source_commit:
        raise ValueError("checkout HEAD does not match published source freeze commit")
    staging = json.loads((ROOT / "STAGING.json").read_text())
    if staging["allocation"] != ALLOCATION:
        raise ValueError("staging identity mismatch")
    evidence = ROOT / "formal"
    evidence.mkdir()  # Refuse a second allocation, including after a partial failure.
    dump(evidence / "CONSUMED.json", {"allocation": ALLOCATION, "source_commit": source_commit,
                                   "started_at_utc": datetime.now(timezone.utc).isoformat()})
    for role in ("candidate", "legacy", "auditor"):
        listing = remote("find", OUTPUT + "/" + role, "-type", "f").strip()
        if listing:
            raise ValueError("formal output is occupied: " + role)
        for item in staging["custody"][role]["sha256sum"].splitlines():
            wanted, path = item.split("  ", 1)
            if remote("sha256sum", path).strip() != wanted + "  " + path:
                raise ValueError("guest source changed")
        cmd = [ORB, "run", "-m", VM, *command(role)]
        before = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(cmd, capture_output=True, text=True)
        dump(evidence / (role + ".receipt.json"), {"command": cmd, "started_at_utc": before,
             "finished_at_utc": datetime.now(timezone.utc).isoformat(), "exit_code": result.returncode,
             "docker_stdout": result.stdout, "docker_stderr": result.stderr})
        inspection = json.loads(remote("docker", "inspect", NAME + "-" + role))
        dump(evidence / (role + ".inspect.json"), inspection)
        subprocess.run([ORB, "pull", "-m", VM, OUTPUT + "/" + role, str(evidence) + "/"], check=True)
        print(role, "exit=" + str(result.returncode), "container=" + inspection[0]["Id"], flush=True)
        if result.returncode != 0:
            raise SystemExit("STOP: allocation consumed; no retry; downstream not started")
    print("FORMAL_SEQUENCE_COMPLETE (not a live-interface result)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("stage", "execute", "commands"))
    parser.add_argument("--source-commit")
    args = parser.parse_args()
    if args.mode == "stage":
        stage()
    elif args.mode == "execute":
        if not args.source_commit or len(args.source_commit) != 40:
            parser.error("--source-commit requires the frozen Git commit SHA")
        execute(args.source_commit)
    else:
        print(json.dumps({role: command(role) for role in ("candidate", "legacy", "auditor")}, indent=2))
