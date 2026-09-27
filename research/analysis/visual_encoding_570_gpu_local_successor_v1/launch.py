from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


OLLAMA_IMAGE = "sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551"
HELPER_IMAGE = "sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261"
MODEL_DIGEST = "fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1"
CONTAINER = "agent-interface-570-r4-local-ollama"
NETWORK = "agent-interface-570-r4-local-internal"


def run(argv, *, check=True, capture=False):
    cp = subprocess.run(argv, text=True, capture_output=capture, timeout=600)
    if check and cp.returncode:
        raise RuntimeError(f"command failed rc={cp.returncode}: {argv[0]} {argv[1:5]}\n{cp.stderr if capture else ''}")
    return cp


def inspect_missing(kind: str, name: str) -> bool:
    cp = run(["docker", kind, "inspect", name], check=False, capture=True)
    if cp.returncode == 0:
        raise SystemExit(f"owned R4 {kind} name already exists; refuse to adopt: {name}")
    if "No such" not in cp.stderr and "not found" not in cp.stderr.lower():
        raise RuntimeError(f"cannot establish {kind} name is unused: {cp.stderr}")
    return True


def helper(root: Path, evidence: Path, net: str, script: str, *args: str):
    argv = ["docker", "run", "--rm", "--platform", "linux/amd64", "--network", net,
            "--cpus", "2", "--memory", "4g", "--pids-limit", "64",
            "--mount", f"type=bind,source={root},target=/src,readonly",
            "--mount", f"type=bind,source={evidence},target=/out",
            "--mount", f"type=bind,source={evidence / 'data'},target=/data,readonly",
            "--entrypoint", "python", HELPER_IMAGE, f"/src/{script}", *args]
    return run(argv, check=False, capture=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    args = p.parse_args()
    root, evidence, font = args.root.resolve(), args.evidence.resolve(), args.font.resolve()
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    for filename, expected in freeze["source_sha256"].items():
        import hashlib
        actual = hashlib.sha256((root / filename).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"frozen source mismatch: {filename}")
    if not (evidence / "data" / "PREFORMAL.json").is_file():
        raise SystemExit("PREFORMAL.json missing; no model request")
    if (evidence / "baseline.json").exists() or (evidence / "formal").exists():
        raise SystemExit("evidence output already exists; refuse rerun")
    evidence.mkdir(parents=True, exist_ok=True)
    inspect_missing("network", NETWORK)
    inspect_missing("container", CONTAINER)
    run(["docker", "network", "create", "--internal", NETWORK])
    models = Path(os.environ.get("OLLAMA_MODELS_HOST", r"C:\Users\junny\.ollama\models"))
    run(["docker", "run", "-d", "--name", CONTAINER, "--platform", "linux/amd64",
         "--network", NETWORK, "--network-alias", "ollama", "--gpus", "all",
         "--mount", f"type=bind,source={models},target=/models,readonly",
         "--env", "OLLAMA_MODELS=/models", "--env", "OLLAMA_NO_CLOUD=true",
         "--env", "OLLAMA_NUM_PARALLEL=1", OLLAMA_IMAGE, "serve"])
    (evidence / "commands.json").write_text(json.dumps({
        "network": ["docker", "network", "create", "--internal", NETWORK],
        "ollama": ["docker", "run", "-d", "--platform", "linux/amd64", "--network", NETWORK,
                   "--network-alias", "ollama", "--gpus", "all", "--mount", "<LOCAL_OLLAMA_MODELS>:/models:ro",
                   "--env", "OLLAMA_NO_CLOUD=true", "<OLLAMA_IMAGE_ID>", "serve"],
        "helper": "docker run --rm --platform linux/amd64 --network <R4_INTERNAL_NETWORK> --cpus 2 --memory 4g --pids-limit 64 --mount <FROZEN_SOURCE>:/src:ro --mount <EVIDENCE>:/out --mount <EVIDENCE_DATA>:/data:ro --entrypoint python <PINNED_HELPER_IMAGE> /src/model_runner.py --mode <construction|formal>"
    }, indent=2) + "\n", encoding="utf-8")
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        cp = run(["docker", "exec", CONTAINER, "ollama", "list"], check=False, capture=True)
        if cp.returncode == 0:
            break
        time.sleep(1)
    else:
        raise SystemExit("Ollama readiness timeout; no model request")
    start_logs = run(["docker", "logs", CONTAINER], capture=True)
    (evidence / "ollama-start.log").write_text(start_logs.stdout + start_logs.stderr, encoding="utf-8")
    baseline = run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"], capture=True)
    ps = run(["docker", "exec", CONTAINER, "ollama", "ps"], capture=True)
    try:
        used, util = [int(v.strip()) for v in baseline.stdout.strip().splitlines()[0].split(",")]
    except (IndexError, ValueError):
        raise SystemExit("cannot parse empty-server GPU baseline; no model request")
    if len(ps.stdout.splitlines()) > 1:
        raise SystemExit("model already resident before construction; no model request")
    (evidence / "baseline.json").write_text(json.dumps({"memory_used_mib": used, "gpu_utilization_percent": util,
        "nvidia_smi_raw": baseline.stdout, "ollama_ps_raw": ps.stdout, "baseline_is_empty_server": True}, indent=2) + "\n", encoding="utf-8")
    sampler = subprocess.Popen([sys.executable, str(root / "sampler.py"), "--container", CONTAINER,
                               "--out", str(evidence / "sampler.jsonl"), "--stop-file", str(evidence / "STOP_SAMPLER")])
    time.sleep(1.0)
    identity = helper(root, evidence, NETWORK, "model_runner.py", "--mode", "identity")
    if identity.returncode:
        raise SystemExit(f"cached model identity mismatch; no inference requested: {identity.stderr}")
    identity_data = json.loads((evidence / "model_identity.json").read_text(encoding="utf-8"))
    if identity_data["models"][0]["digest"] != MODEL_DIGEST:
        raise SystemExit("cached model digest mismatch; no inference requested")
    construction = helper(root, evidence, NETWORK, "model_runner.py", "--mode", "construction")
    (evidence / "construction-helper.stdout.txt").write_text(construction.stdout, encoding="utf-8")
    (evidence / "construction-helper.stderr.txt").write_text(construction.stderr, encoding="utf-8")
    if construction.returncode:
        raise SystemExit("construction call failed; formal requests remain 0")
    time.sleep(0.5)
    samples = [json.loads(line) for line in (evidence / "sampler.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    call = json.loads((evidence / "construction" / "construction-offcenter.json").read_text(encoding="utf-8"))
    placement = [s for s in samples if call["started_utc_ns"] <= s["utc_ns"] <= call["ended_utc_ns"]
                 and isinstance(s.get("memory_used_mib"), int) and s["memory_used_mib"] > used
                 and "gpu" in s.get("ollama_ps_stdout", "").lower()]
    (evidence / "construction-gate.json").write_text(json.dumps({"gpu_baseline_mib": used,
        "interval_sample_count": sum(call["started_utc_ns"] <= s["utc_ns"] <= call["ended_utc_ns"] for s in samples),
        "positive_gpu_placement_samples": len(placement), "construction_interval": [call["started_utc_ns"], call["ended_utc_ns"]]}, indent=2) + "\n", encoding="utf-8")
    if not placement:
        raise SystemExit("STOP_GPU_OFFLOAD_UNAVAILABLE; formal requests remain 0")
    formal = helper(root, evidence, NETWORK, "model_runner.py", "--mode", "formal")
    (evidence / "formal-helper.stdout.txt").write_text(formal.stdout, encoding="utf-8")
    (evidence / "formal-helper.stderr.txt").write_text(formal.stderr, encoding="utf-8")
    (evidence / "STOP_SAMPLER").write_text("formal helper finished\n", encoding="utf-8")
    sampler.wait(timeout=15)
    if formal.returncode:
        raise SystemExit("formal block ended on first error; no retries or seed replacement")
    logs = run(["docker", "logs", CONTAINER], check=False, capture=True)
    (evidence / "ollama-final.log").write_text(logs.stdout + logs.stderr, encoding="utf-8")
    audit = run([sys.executable, str(root / "audit.py"), "--root", str(evidence), "--out", str(evidence / "AUDIT.json")], capture=True)
    (evidence / "audit.stdout.txt").write_text(audit.stdout, encoding="utf-8")
    (evidence / "audit.stderr.txt").write_text(audit.stderr, encoding="utf-8")
    run(["docker", "stop", CONTAINER], check=True)
    if audit.returncode:
        raise SystemExit("independent raw audit failed; preserved evidence and stopped own container")
    print((evidence / "AUDIT.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()

