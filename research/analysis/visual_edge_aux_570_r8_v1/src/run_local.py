#!/usr/bin/env python3
"""Run construction then one formal local-Docker GPU comparison, never retry."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC, INPUTS = ROOT / "src", ROOT / "inputs"
RESULTS = ROOT / "results"
CONSTRUCTION_OUT = ROOT / "construction-out"
FORMAL_OUT = ROOT / "formal-out"
OLLAMA_IMAGE = "ollama/ollama:0.34.4"
OLLAMA_ID = "sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551"
HELPER_IMAGE = "agent-interface-real-robustness-2912:cpu"
HELPER_ID = "sha256:c429dd941b668e2689a99ecc6b9717093647489e755cdbd8eb6e1594e4497aaf"
MODEL_DIGEST = "fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1"
FONT = Path(r"C:\Windows\Fonts\arial.ttf")
MODEL_STORE = Path(r"C:\Users\junny\.ollama\models")
NETWORK = "ai-venc-r8-internal"
SERVICE = "ai-venc-r8-ollama"


def run(cmd, check=True):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    if check and p.returncode:
        raise RuntimeError(f"COMMAND_EXIT_{p.returncode}: {cmd[0]} {cmd[1:]}\n{p.stderr[-2000:]}")
    return p


def inspect_id(image):
    p = run(["docker", "image", "inspect", image, "--format", "{{.Id}}"])
    return p.stdout.strip()


class Sampler:
    def __init__(self, path):
        self.path = path
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.rows = []
        self.lock = threading.Lock()

    def sample(self):
        p = run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"], check=False)
        row = {"timestamp_ns": time.time_ns(), "exit_code": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
        try:
            mem, util = [int(v.strip()) for v in p.stdout.strip().splitlines()[0].split(",")]
            row.update({"memory_used_mib": mem, "utilization_percent": util})
        except Exception:
            row.update({"memory_used_mib": -1, "utilization_percent": -1})
        with self.lock:
            self.rows.append(row)
            with self.path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        return row

    def loop(self):
        while not self.stop_event.is_set():
            self.sample()
            self.stop_event.wait(0.2)

    def start(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")
        baseline = self.sample()
        self.thread.start()
        return baseline

    def close(self):
        self.stop_event.set()
        self.thread.join(timeout=5)
        self.path.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in self.rows), encoding="utf-8")


def docker_helper(split, outdir, network):
    if outdir.exists() and any(outdir.iterdir()):
        raise RuntimeError("STOP_OUTPUT_NOT_EMPTY:" + str(outdir))
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = ["docker", "run", "--rm", "--pull=never", "--network", network,
           "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=64m",
           "-e", "OLLAMA_HOST=http://ollama-r8:11434", "-e", "FONT_PATH=/font/arial.ttf",
           "--mount", f"type=bind,source={SRC.as_posix()},target=/src,readonly",
           "--mount", f"type=bind,source={INPUTS.as_posix()},target=/inputs,readonly",
           "--mount", f"type=bind,source={FONT.as_posix()},target=/font/arial.ttf,readonly",
           "--mount", f"type=bind,source={outdir.as_posix()},target=/out",
           "--entrypoint", "python", HELPER_IMAGE, "/src/runner.py", "--split", split]
    return run(cmd, check=False)


def audit_container(split, outdir, baseline_mib):
    cmd = ["docker", "run", "--rm", "--pull=never", "--network", "none", "--read-only",
           "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=64m",
           "--mount", f"type=bind,source={SRC.as_posix()},target=/src,readonly",
           "--mount", f"type=bind,source={INPUTS.as_posix()},target=/inputs,readonly",
           "--mount", f"type=bind,source={outdir.as_posix()},target=/out",
           "--entrypoint", "python", HELPER_IMAGE, "/src/audit.py",
           "--manifest", "/inputs/manifest.json", "--records", "/out/raw_calls.jsonl",
           "--samples", "/out/gpu_samples.jsonl", "--baseline-mib", str(baseline_mib),
           "--split", split, "--output", "/out/audit.json"]
    return run(cmd, check=False)


def move_samples(sampler_path, outdir):
    target = outdir / "gpu_samples.jsonl"
    target.write_bytes(sampler_path.read_bytes())


def verify_local_freeze():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    for rel, expected in freeze["sha256"].items():
        p = ROOT / rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise RuntimeError("STOP_SOURCE_FREEZE_MISMATCH:" + rel)
    if inspect_id(OLLAMA_IMAGE) != OLLAMA_ID or inspect_id(HELPER_IMAGE) != HELPER_ID:
        raise RuntimeError("STOP_IMAGE_ID_MISMATCH")
    return freeze


def write_text(path, content):
    path.write_text(content, encoding="utf-8", newline="\n")


def main():
    if RESULTS.exists() and any(RESULTS.iterdir()):
        raise RuntimeError("STOP_RUN_RESULTS_ALREADY_EXIST")
    RESULTS.mkdir(exist_ok=True)
    freeze = verify_local_freeze()
    if inspect_id(OLLAMA_IMAGE) != OLLAMA_ID or inspect_id(HELPER_IMAGE) != HELPER_ID:
        raise RuntimeError("STOP_IMAGE_ID_MISMATCH")
    nvs = run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"])
    if "RTX 3080 Laptop GPU" not in nvs.stdout or not MODEL_STORE.is_dir():
        raise RuntimeError("STOP_GPU_OR_MODEL_STORE_UNAVAILABLE")
    sampler_path = RESULTS / "gpu_samples.jsonl"
    sampler = Sampler(sampler_path)
    baseline = sampler.start()
    baseline_mib = baseline["memory_used_mib"]
    write_text(RESULTS / "preflight.txt", json.dumps({"gpu": nvs.stdout.strip(), "baseline": baseline, "images": {OLLAMA_IMAGE: OLLAMA_ID, HELPER_IMAGE: HELPER_ID}, "main": freeze["base_main"]}, indent=2) + "\n")
    created_network = created_service = False
    formal_started = False
    disposition = "STOP_SETUP"
    try:
        if baseline_mib < 0 or baseline_mib > 1024 or baseline["utilization_percent"] > 10:
            raise RuntimeError("STOP_GPU_NOT_IDLE_AT_BASELINE")
        if run(["docker", "ps", "--format", "{{.Names}}"]).stdout.splitlines().count(SERVICE):
            raise RuntimeError("STOP_OWN_SERVICE_NAME_ALREADY_EXISTS")
        run(["docker", "network", "create", "--internal", NETWORK]); created_network = True
        cmd = ["docker", "run", "-d", "--pull=never", "--name", SERVICE, "--gpus", "all", "--network", NETWORK, "--network-alias", "ollama-r8",
               "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,size=2g",
               "--mount", f"type=bind,source={MODEL_STORE.as_posix()},target=/models,readonly",
               "-e", "HOME=/tmp/ollama-home", "-e", "OLLAMA_MODELS=/models", "-e", "OLLAMA_HOST=0.0.0.0:11434", "-e", "OLLAMA_NO_CLOUD=1", OLLAMA_IMAGE]
        run(cmd); created_service = True
        ready = False
        for _ in range(120):
            p = run(["docker", "exec", SERVICE, "ollama", "list"], check=False)
            if p.returncode == 0:
                ready = True; break
            time.sleep(0.5)
        if not ready:
            raise RuntimeError("STOP_OLLAMA_STARTUP_TIMEOUT")
        construction = docker_helper("construction", CONSTRUCTION_OUT, NETWORK)
        write_text(RESULTS / "construction.stdout.txt", construction.stdout)
        write_text(RESULTS / "construction.stderr.txt", construction.stderr)
        if construction.returncode != 0:
            raise RuntimeError(f"STOP_CONSTRUCTION_RUNNER_EXIT_{construction.returncode}")
        time.sleep(0.5)
        move_samples(sampler_path, CONSTRUCTION_OUT)
        ca = audit_container("construction", CONSTRUCTION_OUT, baseline_mib)
        write_text(RESULTS / "construction.audit.stdout.txt", ca.stdout)
        write_text(RESULTS / "construction.audit.stderr.txt", ca.stderr)
        if ca.returncode != 0:
            raise RuntimeError(f"STOP_CONSTRUCTION_AUDIT_EXIT_{ca.returncode}")
        audit_c = json.loads((CONSTRUCTION_OUT / "audit.json").read_text(encoding="utf-8"))
        if audit_c["decision"] != "CONSTRUCTION_AUDIT_PASS" or audit_c["errors"]:
            raise RuntimeError("STOP_CONSTRUCTION_AUDIT_NOT_PASS")
        if (FORMAL_OUT.exists() and any(FORMAL_OUT.iterdir())):
            raise RuntimeError("STOP_FORMAL_OUTPUT_NOT_EMPTY")
        formal_started = True
        formal = docker_helper("formal", FORMAL_OUT, NETWORK)
        write_text(RESULTS / "formal.stdout.txt", formal.stdout)
        write_text(RESULTS / "formal.stderr.txt", formal.stderr)
        if formal.returncode != 0:
            raise RuntimeError(f"STOP_FORMAL_RUNNER_EXIT_{formal.returncode}")
        disposition = "FORMAL_RUN_COMPLETE_AUDIT_PENDING"
        sampler.close()
        move_samples(sampler_path, FORMAL_OUT)
        fa = audit_container("formal", FORMAL_OUT, baseline_mib)
        write_text(RESULTS / "formal.audit.stdout.txt", fa.stdout)
        write_text(RESULTS / "formal.audit.stderr.txt", fa.stderr)
        if fa.returncode != 0:
            raise RuntimeError(f"HOLD_FORMAL_AUDIT_EXIT_{fa.returncode}")
        audit_f = json.loads((FORMAL_OUT / "audit.json").read_text(encoding="utf-8"))
        disposition = audit_f["decision"]
        print(json.dumps({"construction": audit_c["decision"], "formal": disposition, "errors": audit_f["errors"], "metrics": audit_f["metrics"]}, sort_keys=True))
    except Exception as exc:
        disposition = str(exc).split(":", 1)[0]
        write_text(RESULTS / "STOP.txt", str(exc) + "\n")
        print("STOP:", exc)
        raise
    finally:
        sampler.close()
        if created_service:
            run(["docker", "stop", "--time", "3", SERVICE], check=False)
            run(["docker", "rm", SERVICE], check=False)
        if created_network:
            run(["docker", "network", "rm", NETWORK], check=False)
        write_text(RESULTS / "disposition.txt", disposition + "\n")


if __name__ == "__main__":
    main()
