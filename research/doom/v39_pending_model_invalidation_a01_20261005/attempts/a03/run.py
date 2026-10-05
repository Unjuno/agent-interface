"""Run candidate and independent audit in separate offline WSLc containers."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
OUT = PACKAGE / "results" / "pending-loop-a03"
IMAGE = "agent-interface/native-suite-wslc-a08:20261004"
IMAGE_ID = "sha256:1b4a8bd7c0fe372cc0cafa74af433b8ae1f73f1bee0f11a028f126b08b2c128a"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(name, target):
    mount = str(ROOT).replace("\\", "/")
    return ["wslc.exe", "run", "--rm", "--pull", "never", "--network", "none",
            "--cpus", "1", "--name", name,
            "--mount", f"type=bind,source={mount},target=/src,readonly",
            "--workdir", "/src",
            "--env", "PYTHONPATH=/src/research/doom:/src/research/live_control:/src",
            "--entrypoint", "python", IMAGE, "-B", target]


def main():
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    resolved = subprocess.check_output(["git", "rev-parse", freeze["repository_commit"]], cwd=ROOT, text=True).strip()
    if resolved != freeze["repository_commit"]:
        raise SystemExit("frozen source commit unavailable on host")
    image_rows = [json.loads(line) for line in subprocess.check_output(
        ["wslc.exe", "image", "list", "--format", "json"], text=True).splitlines() if line.strip()]
    if not any(row.get("Repository") == "agent-interface/native-suite-wslc-a08" and
               row.get("Tag") == "20261004" and IMAGE_ID.startswith("sha256:" + row.get("ID", ""))
               for row in image_rows):
        raise SystemExit("frozen WSLc image ID unavailable")
    for name, digest in freeze["study_scripts_sha256"].items():
        if sha(PACKAGE / name) != digest:
            raise SystemExit("study script changed after freeze: " + name)
    for name, digest in freeze["implementation_file_sha256"].items():
        if sha(ROOT / name) != digest:
            raise SystemExit("implementation source changed after freeze: " + name)
    if OUT.exists():
        raise SystemExit("output already exists; refusing to overwrite first outcome")
    OUT.mkdir(parents=True)
    receipts = []
    for label, target in (("candidate", "research/doom/v39_pending_model_invalidation_a01_20261005/candidate.py"),
                          ("audit", "research/doom/v39_pending_model_invalidation_a01_20261005/audit.py")):
        argv = command("v39-pending-a03-" + label, target)
        started = time.time_ns()
        run = subprocess.run(argv, cwd=ROOT, capture_output=True)
        finished = time.time_ns()
        (OUT / (label + ".stdout.json")).write_bytes(run.stdout)
        (OUT / (label + ".stderr.log")).write_bytes(run.stderr)
        redacted_mount = f"source={str(ROOT).replace(chr(92), '/')},target=/src,readonly"
        public = [x.replace(redacted_mount, "source=<repo>,target=/src,readonly") for x in argv]
        receipts.append({"label": label, "argv": public,
                         "executed_argv_sha256": hashlib.sha256(
                             json.dumps(argv, separators=(",", ":")).encode()).hexdigest(),
                         "mount_path_redacted": True, "started_unix_ns": started,
                         "finished_unix_ns": finished, "returncode": run.returncode,
                         "stdout_sha256": hashlib.sha256(run.stdout).hexdigest(),
                         "stderr_sha256": hashlib.sha256(run.stderr).hexdigest(),
                         "image": IMAGE, "image_id": IMAGE_ID,
                         "network": "none", "cpu_limit": 1, "source_mount": "read-only"})
        print(label + ": exit=" + str(run.returncode))
        print(run.stdout.decode("utf-8", errors="replace"))
        if run.stderr:
            print(run.stderr.decode("utf-8", errors="replace"))
        if run.returncode != 0:
            (OUT / "runs.json").write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
            return run.returncode
        if label == "candidate":
            (OUT / "candidate.raw.json").write_bytes(run.stdout)
    (OUT / "runs.json").write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

