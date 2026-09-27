"""Obstac/OrbStack launcher for one immutable construction or formal allocation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
IMAGE = "issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--construction", action="store_true")
    args = parser.parse_args()
    stage = "construction" if args.construction else "formal"
    output, exchange = ROOT / stage / "output", ROOT / stage / "exchange"
    output.mkdir(parents=True, exist_ok=True)
    exchange.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()) or any(exchange.iterdir()):
        raise SystemExit("STOP_OUTPUT_OR_EXCHANGE_NOT_EMPTY")
    freeze_path = ROOT / "FREEZE.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    image_info = subprocess.check_output(["docker", "--context", "orbstack", "image", "inspect", IMAGE,
                                          "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"], text=True).strip()
    if image_info != freeze["image_id"] + " linux/arm64":
        raise SystemExit("STOP_IMAGE_IDENTITY_MISMATCH:" + image_info)
    env = {"OBSTAC_SOURCE_COMMIT": freeze["base_commit"], "OBSTAC_IMAGE_ID": freeze["image_id"],
           "OBSTAC_FREEZE_SHA256": sha(freeze_bytes), "CONSTRUCTION_ONLY": "1" if args.construction else "0"}
    bridge_cmd = [sys.executable, str(ROOT / "host_bridge.py"), str(exchange), str(output / "images"), str(output)]
    if args.construction:
        bridge_cmd.append("--mock")
    output.mkdir(parents=True, exist_ok=True)
    bridge_log = (output / "bridge.log").open("w")
    bridge = subprocess.Popen(bridge_cmd, stdout=bridge_log, stderr=subprocess.STDOUT, text=True)
    docker_cmd = ["docker", "--context", "orbstack", "run", "--rm", "--pull=never", "--platform", "linux/arm64",
                  "--network", "none", "--read-only", "--workdir", "/tmp",
                  "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m", "--pids-limit", "32", "--memory", "512m",
                  "--cpus", "1", "--cap-drop", "ALL", "--security-opt", "no-new-privileges"]
    for key, value in env.items():
        docker_cmd.extend(["-e", f"{key}={value}"])
    docker_cmd.extend(["-v", f"{ROOT}:/src:ro", "-v", f"{freeze_path}:/freeze/FREEZE.json:ro",
                       "-v", f"{ROOT / 'PREREGISTRATION.md'}:/freeze/PREREGISTRATION.md:ro",
                       "-v", f"{output}:/out:rw", "-v", f"{exchange}:/exchange:rw", IMAGE, "python", "/src/runner.py"])
    (output / "OBSTAC_EXECUTION.json").write_text(json.dumps({"allocation": freeze["allocation"], "docker_context": "orbstack",
        "docker_argv": docker_cmd, "obstac_environment": env, "network": "none", "source_read_only": True,
        "formal_invocation_count": 0 if args.construction else 1, "request_budget": 9, "retry_budget": 0},
        indent=2, sort_keys=True) + "\n")
    try:
        subprocess.run(docker_cmd, check=True)
        bridge.wait(timeout=20)
        if bridge.returncode:
            raise SystemExit("STOP_HOST_BRIDGE_EXIT:" + str(bridge.returncode))
    except Exception:
        if bridge.poll() is None:
            bridge.terminate()
            try:
                bridge.wait(timeout=3)
            except subprocess.TimeoutExpired:
                bridge.kill()
                bridge.wait()
        raise
    finally:
        bridge_log.close()
    print(json.dumps({"allocation": freeze["allocation"], "stage": stage,
                      "formal_invocation_count": 0 if args.construction else 1}, sort_keys=True))


if __name__ == "__main__":
    main()
