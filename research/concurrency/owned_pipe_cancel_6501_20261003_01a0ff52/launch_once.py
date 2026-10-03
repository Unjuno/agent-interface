"""Explicitly owned OrbStack guest; no default daemon, pull, or formal retry."""
import datetime
import hashlib
import io
import json
import pathlib
import subprocess
import sys
import tarfile

GUEST = "research-6501-async-01a0ff52-70ab"
IMAGE = "python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016"
SOURCE = "/root/6501-pipe-source-a01"
OUTPUT = "/root/6501-pipe-a01"
CONTAINER = "6501-owned-pipe-a01-01a0ff52-70ab"
ALLOCATION = "6501-OWNED-PIPE-ORBSTACK-A01-20261003-01a0ff52-70ab"


def remote(args, **kwargs):
    return subprocess.run(["orb", "-m", GUEST, "-u", "root", *args], capture_output=True, timeout=kwargs.pop("timeout", 15), **kwargs)


def checked(args, **kwargs):
    r = remote(args, **kwargs)
    if r.returncode:
        raise RuntimeError("remote command failed: " + str(args) + ": " + r.stderr.decode())
    return r


def main():
    root = pathlib.Path(__file__).resolve().parent
    source_commit = sys.argv[1]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if source_commit != head:
        raise RuntimeError("source-freeze commit does not match checked-out HEAD")
    freeze_bytes = (root / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    for name, pin in freeze["source_sha256"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != pin:
            raise RuntimeError("source mismatch: " + name)
    out = root / "results"
    out.mkdir(exist_ok=False)
    attempt = {"allocation": ALLOCATION, "source_commit": head, "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
               "candidate_attempts": 0, "auditor_attempts": 0, "guest": GUEST, "status": "PREPARED"}
    def save():
        (out / "host_attempt.json").write_text(json.dumps(attempt, indent=2) + "\n")
    save()
    checked(["mkdir", SOURCE, OUTPUT])
    packed = io.BytesIO()
    with tarfile.open(fileobj=packed, mode="w") as archive:
        for name in [*freeze["source_sha256"], "FREEZE.json"]:
            archive.add(root / name, arcname=name)
    checked(["tar", "-xf", "-", "-C", SOURCE], input=packed.getvalue())
    create = ["docker", "create", "--pull", "never", "--name", CONTAINER, "--label", "allocation=" + ALLOCATION,
              "--network", "none", "--read-only", "--cpus", "0.25", "--memory", "128m", "--pids-limit", "32",
              "--mount", "type=bind,source=" + SOURCE + ",target=/source,readonly",
              "--mount", "type=bind,source=" + OUTPUT + ",target=/out", IMAGE, "python", "-B", "/source/driver.py"]
    attempt["create_command"] = ["orb", "-m", GUEST, "-u", "root", *create]
    attempt["container_id"] = checked(create).stdout.decode().strip()
    inspect = checked(["docker", "inspect", CONTAINER]).stdout
    (out / "container_before.json").write_bytes(inspect)
    config = json.loads(inspect)[0]
    host = config["HostConfig"]
    if not (host["NetworkMode"] == "none" and host["ReadonlyRootfs"] is True and host["NanoCpus"] == 250000000
            and host["Memory"] == 134217728 and host["PidsLimit"] == 32
            and {m["Destination"]: m["RW"] for m in config["Mounts"]} == {"/source": False, "/out": True}):
        raise RuntimeError("STOP: inspected resource/mount configuration mismatch")
    attempt["status"] = "SENT_ONCE"
    attempt["started_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    attempt["candidate_attempts"] = 1  # conservative count before external send
    save()
    try:
        run = remote(["docker", "start", "--attach", CONTAINER], timeout=30)
        (out / "container.stdout.txt").write_bytes(run.stdout)
        (out / "container.stderr.txt").write_bytes(run.stderr)
        attempt["exit_code"] = run.returncode
    except subprocess.TimeoutExpired as exc:
        attempt["status"] = "STOP_OUTER_TIMEOUT"
        (out / "container.stdout.txt").write_bytes(exc.stdout or b"")
        (out / "container.stderr.txt").write_bytes(exc.stderr or b"")
        stop = remote(["docker", "stop", "--time", "1", CONTAINER])
        (out / "timeout_stop.stdout.txt").write_bytes(stop.stdout)
        (out / "timeout_stop.stderr.txt").write_bytes(stop.stderr)
        attempt["timeout_stop_exit"] = stop.returncode
    attempt["ended_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (out / "container_after.json").write_bytes(checked(["docker", "inspect", CONTAINER]).stdout)
    payload = checked(["tar", "-cf", "-", "-C", OUTPUT, "."]).stdout
    (out / "guest_output.tar").write_bytes(payload)
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
        for item in archive.getmembers():
            if item.isdir():
                continue
            name = item.name.removeprefix("./")
            if not item.isfile() or "/" in name or name.startswith(".") or (out / name).exists():
                raise RuntimeError("unexpected guest output member: " + name)
            (out / name).write_bytes(archive.extractfile(item).read())
    if (out / "driver_receipts.json").exists():
        receipts = json.loads((out / "driver_receipts.json").read_text())
        attempt["auditor_attempts"] = sum(r["component"] == "auditor" for r in receipts)
    if attempt["status"] == "SENT_ONCE":
        attempt["status"] = "COMPLETE" if attempt.get("exit_code") == 0 else "STOP_COMPONENT_FAILURE"
    save()
    print(json.dumps(attempt))
    return 0 if attempt["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
