"""Host launcher: one bounded local-model run with an isolated container runner."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
IMAGE = "issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51"


def call(args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def run(construction):
    out = HERE / ("construction-final/output" if construction else "output")
    exchange = HERE / ("construction-final/exchange" if construction else "exchange")
    out.mkdir(parents=True, exist_ok=True)
    exchange.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()) or any(exchange.iterdir()):
        raise SystemExit("STOP_OUTPUT_OR_EXCHANGE_NOT_EMPTY")
    tag = subprocess.check_output(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"], text=True).strip()
    if not tag.endswith("linux/arm64"):
        raise SystemExit("STOP_CONTAINER_IMAGE_IDENTITY_MISMATCH:" + tag)
    bridge_cmd = [sys.executable, str(HERE / "host_bridge.py"), str(exchange), str(out)]
    if construction:
        bridge_cmd.append("--mock")
    log = (out / "bridge.log").open("w")
    bridge = subprocess.Popen(bridge_cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    docker_cmd = ["docker", "run", "--rm", "--pull=never", "--platform", "linux/arm64", "--network", "none",
                  "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m", "--pids-limit", "32",
                  "--memory", "512m", "--cpus", "1", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                  "-e", "CONSTRUCTION_ONLY=" + ("1" if construction else "0"),
                  "-v", f"{HERE}:/src:ro", "-v", f"{out}:/out:rw", "-v", f"{exchange}:/exchange:rw",
                  "-v", f"{HERE / 'FREEZE.json'}:/freeze/FREEZE.json:ro", IMAGE, "python", "/src/runner.py"]
    try:
        call(docker_cmd)
        bridge.wait(timeout=15)
        if bridge.returncode != 0:
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
        log.close()
    if not (exchange / "BRIDGE_SUMMARY.json").exists():
        raise SystemExit("STOP_BRIDGE_SUMMARY_MISSING")
    print(json.dumps({"docker_image": tag, "construction": construction, "calls": 9}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--construction", action="store_true")
    run(parser.parse_args().construction)
