"""Obstac/OrbStack one-shot launcher; no fallback or retry."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
IMAGE = "issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--construction", action="store_true")
    args = parser.parse_args()
    stage = "construction" if args.construction else "formal"
    out, exchange = ROOT / stage / "output", ROOT / stage / "exchange"
    if any(out.iterdir()) or any(exchange.iterdir()):
        raise SystemExit("STOP_RESULT_MOUNT_NOT_EMPTY")
    freeze_path = ROOT / "FREEZE.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    image_id = subprocess.check_output(["docker", "--context", "orbstack", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"], text=True).strip()
    if image_id != freeze["image_id"] + " linux/arm64":
        raise SystemExit("STOP_OBSTAC_IMAGE_MISMATCH:" + image_id)
    bridge_command = [sys.executable, str(SRC / "bridge.py"), str(exchange), str(out)]
    if args.construction:
        bridge_command.append("--mock")
    log = (out / "bridge.log").open("w")
    bridge = subprocess.Popen(bridge_command, stdout=log, stderr=subprocess.STDOUT, text=True)
    env = {"OBSTAC_SOURCE_COMMIT": freeze["base_commit"], "OBSTAC_IMAGE_ID": freeze["image_id"],
           "OBSTAC_FREEZE_SHA256": sha(freeze_bytes), "OBSTAC_CONSTRUCTION": "1" if args.construction else "0"}
    command = ["docker", "--context", "orbstack", "run", "--rm", "--pull=never", "--platform", "linux/arm64",
               "--network", "none", "--read-only", "--workdir", "/tmp", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
               "--pids-limit", "32", "--memory", "512m", "--cpus", "1", "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges"]
    for key, value in env.items():
        command += ["-e", f"{key}={value}"]
    command += ["-v", f"{SRC}:/task:ro", "-v", f"{freeze_path}:/freeze/FREEZE.json:ro",
                "-v", f"{ROOT / 'PREREGISTRATION.md'}:/freeze/PREREGISTRATION.md:ro",
                "-v", f"{out}:/out:rw", "-v", f"{exchange}:/exchange:rw", IMAGE, "python", "/task/probe.py"]
    (out / "OBSTAC_EXECUTION.json").write_text(json.dumps({"allocation": freeze["allocation"],
        "docker_context": "orbstack", "docker_argv": command, "obstac_environment": env,
        "formal_invocation_count": 0 if args.construction else 1, "network": "none",
        "source_read_only": True, "dedicated_result_mount": True}, indent=2, sort_keys=True) + "\n")
    try:
        subprocess.run(command, check=True)
        bridge.wait(timeout=10)
        if bridge.returncode:
            raise SystemExit("STOP_BRIDGE_EXIT:" + str(bridge.returncode))
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
