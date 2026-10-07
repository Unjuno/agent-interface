"""Once-only host subprocess capture; contains no runtime-specific authority."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def execute(argv, output, binding=None):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("output already occupied: " + str(output))
    output.mkdir(parents=True, exist_ok=True)
    attempt = {"argv": argv, "started_utc": datetime.now(timezone.utc).isoformat()}
    if binding is not None:
        attempt["binding"] = binding
    (output / "attempt.json").write_text(
        json.dumps(attempt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    started = time.perf_counter()
    launch_error = None
    try:
        process = subprocess.run(argv, capture_output=True)
        stdout, stderr, exit_code = process.stdout, process.stderr, process.returncode
    except OSError as exc:
        stdout, stderr, exit_code, launch_error = b"", b"", None, str(exc)
    (output / "stdout.bin").write_bytes(stdout)
    (output / "stderr.bin").write_bytes(stderr)
    receipt = {**attempt, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "wall_seconds": time.perf_counter() - started, "exit_code": exit_code,
        "launch_error": launch_error,
        "output_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(output.iterdir()) if p.is_file()}}
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def validate_sources(root, hashes):
    actual = {}
    for name, expected in hashes.items():
        actual[name] = hashlib.sha256((Path(root) / name).read_bytes()).hexdigest()
        if actual[name] != expected:
            raise ValueError("STOP_SOURCE_HASH_MISMATCH:" + name)
    return actual


def frozen(role, check_only=False):
    root = Path(__file__).resolve().parent
    repo = root.parents[2]
    freeze_bytes = (root / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    if freeze["freeze_time_utc"].startswith("PENDING"):
        raise ValueError("STOP_FREEZE_INCOMPLETE")
    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args],
            capture_output=True, check=True, text=True).stdout.strip()
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("STOP_SOURCE_WORKTREE_NOT_CLEAN")
    if git("branch", "--show-current") != freeze["branch"]:
        raise ValueError("STOP_BRANCH_MISMATCH")
    hashes = validate_sources(root, freeze["sha256"])
    receipt_dir = Path(freeze["host_paths"][role + "_launch"])
    data_dir = Path(freeze["host_paths"][role + "_data"])
    for path in (receipt_dir, data_dir):
        if path.exists() and any(path.iterdir()):
            raise ValueError("STOP_ROLE_ALREADY_ATTEMPTED")
    binding = {"source_commit": git("rev-parse", "HEAD"),
               "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
               "source_sha256": hashes, "allocation": freeze["allocation"]}
    if role == "auditor":
        prior = Path(freeze["host_paths"]["candidate_launch"]) / "receipt.json"
        candidate = json.loads(prior.read_bytes())
        if candidate["binding"] != binding:
            raise ValueError("STOP_CANDIDATE_SOURCE_BINDING_MISMATCH")
        binding["candidate_raw_sha256"] = hashlib.sha256(
            (Path(freeze["host_paths"]["candidate_data"]) / "candidate_stdout.json").read_bytes()
        ).hexdigest()
    if check_only:
        return {"status": "READY", "role": role, "binding": binding}
    data_dir.mkdir(parents=True, exist_ok=True)
    return execute(freeze["commands"][role], receipt_dir, binding=binding)


if __name__ == "__main__":
    if sys.argv[1] == "--frozen":
        receipt = frozen(sys.argv[2], check_only="--check-only" in sys.argv[3:])
    else:
        receipt = execute(sys.argv[2:], Path(sys.argv[1]))
    print(json.dumps(receipt, sort_keys=True))
    raise SystemExit(0 if receipt.get("status") == "READY" else
                     (receipt["exit_code"] if receipt["exit_code"] is not None else 1))
