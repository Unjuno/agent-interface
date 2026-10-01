"""Host launcher implementing the repository's Obstac/OrbStack contract."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parents[1]
SRC = HERE / "src"
IMAGE = "issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--construction", action="store_true")
    args = parser.parse_args()
    suffix = "construction-final-02" if args.construction else "formal"
    output = HERE / suffix / "output"
    exchange = HERE / suffix / "exchange"
    if any(output.iterdir()) or any(exchange.iterdir()):
        raise SystemExit("STOP_NONEMPTY_OBSTAC_RESULT_MOUNT")
    freeze_path = HERE / "FREEZE.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    image_id = subprocess.check_output(["docker", "--context", "orbstack", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"], text=True).strip()
    if image_id != freeze["image_id"] + " linux/arm64":
        raise SystemExit("STOP_OBSTAC_IMAGE_ID_MISMATCH:" + image_id)
    bridge_cmd = [sys.executable, str(SRC / "host_bridge.py"), str(exchange), str(output)]
    if args.construction:
        bridge_cmd.append("--mock")
    log = (output / "host-bridge.log").open("w")
    bridge = subprocess.Popen(bridge_cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    env_values = {
        "OBSTAC_SOURCE_COMMIT": freeze["base_commit"], "OBSTAC_IMAGE_ID": freeze["image_id"],
        "OBSTAC_FREEZE_SHA256": sha(freeze_bytes), "OBSTAC_CONSTRUCTION": "1" if args.construction else "0",
    }
    command = ["docker", "--context", "orbstack", "run", "--rm", "--pull=never", "--platform", "linux/arm64",
               "--network", "none", "--read-only", "--workdir", "/tmp", "--tmpfs", "/tmp:rw,nosuid,noexec,size=32m",
               "--pids-limit", "32", "--memory", "512m", "--cpus", "1", "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges"]
    for key, value in env_values.items():
        command += ["-e", f"{key}={value}"]
    command += ["-v", f"{SRC}:/task:ro", "-v", f"{freeze_path}:/freeze/FREEZE.json:ro",
                "-v", f"{HERE / 'PREREGISTRATION.md'}:/freeze/PREREGISTRATION.md:ro",
                "-v", f"{output}:/out:rw", "-v", f"{exchange}:/exchange:rw", IMAGE, "python", "/task/runner.py"]
    (output / "OBSTAC_EXECUTION.json").write_text(json.dumps({
        "allocation": freeze["allocation"], "docker_context": "orbstack", "docker_argv": command,
        "obstac_environment": env_values, "formal_invocation_count": 0 if args.construction else 1,
        "network": "none", "source_mount": "read-only", "results_mount": "dedicated-writable",
    }, indent=2, sort_keys=True) + "\n")
    try:
        subprocess.run(command, check=True)
        bridge.wait(timeout=10)
        if bridge.returncode:
            raise SystemExit("STOP_OBSTAC_HOST_BRIDGE_EXIT:" + str(bridge.returncode))
    except Exception:
        if bridge.poll() is None:
            bridge.terminate()
            try:
                bridge.wait(timeout=2)
            except subprocess.TimeoutExpired:
                bridge.kill()
                bridge.wait()
        raise
    finally:
        log.close()
    print(json.dumps({"allocation": freeze["allocation"], "docker_context": "orbstack",
                      "formal_invocation_count": 0 if args.construction else 1}, sort_keys=True))


if __name__ == "__main__":
    main()
