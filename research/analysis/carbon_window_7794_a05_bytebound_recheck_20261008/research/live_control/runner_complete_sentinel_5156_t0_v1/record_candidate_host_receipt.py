"""Bind candidate container execution to its retained local OrbStack receipt."""
import hashlib
import json
import sys
from pathlib import Path

IMAGE = "python@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a"
DIGEST = "sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(results_dir, candidate_exit, container_id, image_id, platform, engine_context, source_dir):
    out, source = Path(results_dir).resolve(), Path(source_dir).resolve()
    argv = ["docker", "run", "--rm", "--pull=never", "--platform=linux/amd64", "--network", "none",
            "--cpus=1", "--memory=256m", "--pids-limit=32", "--read-only", "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=32m", "--cap-drop=ALL", "--security-opt=no-new-privileges",
            "--mount", f"type=bind,source={source},target=/src,readonly",
            "--mount", f"type=bind,source={out},target=/out", "--workdir", "/src",
            "--entrypoint", "/bin/sh", IMAGE, "-ceu",
            "exec python3 -B /src/run_mutation_experiment.py /out"]
    receipt = {
        "schema": "local-container-candidate-receipt-v1",
        "engine_context": engine_context,
        "container_id": container_id,
        "candidate_exit_code": int(candidate_exit),
        "image_id": image_id,
        "image_digest": DIGEST,
        "platform": platform,
        "argv": argv,
        "argv_sha256": hashlib.sha256(json.dumps(argv, separators=(",", ":")).encode()).hexdigest(),
        "stdout_sha256": sha256(out / "container.stdout.txt"),
        "stderr_sha256": sha256(out / "container.stderr.txt"),
        "run_receipt_sha256": sha256(out / "RUN.json") if (out / "RUN.json").is_file() else None,
    }
    (out / "candidate-host-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                                                     encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 8:
        raise SystemExit("usage: record_candidate_host_receipt.py RESULTS EXIT CID IMAGE_ID PLATFORM ENGINE SOURCE")
    raise SystemExit(main(*sys.argv[1:]))
