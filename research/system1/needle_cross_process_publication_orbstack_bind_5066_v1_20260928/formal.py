"""Fail-closed source/image preflight plus exactly one formal and audit run."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

EXP = Path(__file__).resolve().parent
REPO = EXP.parents[2]
SEED = REPO / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json"
IMAGE = "sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
CONTEXT = "orbstack"


def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()


def run(argv): return subprocess.run(argv, text=True, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--preflight-only", action="store_true")
    args = ap.parse_args()
    output = Path(args.output).resolve()
    if not output.is_absolute() or output.exists(): raise RuntimeError("output must be an unused absolute path")
    if sha(SEED.read_bytes()) != "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a":
        raise RuntimeError("seed identity mismatch")
    freeze = json.loads((EXP / "FREEZE.json").read_text())
    source_hashes = freeze["source_sha256"]
    actual = {name: sha((EXP / name).read_bytes()) for name in source_hashes}
    if actual != source_hashes: raise RuntimeError("frozen source hash mismatch")
    source_commit = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    if run(["git", "status", "--porcelain"]).stdout.strip(): raise RuntimeError("formal source checkout is dirty")
    freeze_sha = sha((EXP / "FREEZE.json").read_bytes())
    if args.preflight_only:
        print(json.dumps({"preflight": "PASS_STATIC", "source_commit": source_commit,
                          "freeze_sha256": freeze_sha, "docker_invocations": 0, "output_created": False}))
        return 0
    if run(["docker", "context", "show"]).stdout.strip() != CONTEXT: raise RuntimeError("wrong Docker context")
    inspected = run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"])
    if inspected.returncode or inspected.stdout.strip() != IMAGE + " linux/arm64": raise RuntimeError("pinned image/platform unavailable")
    if run(["docker", "ps", "--quiet"]).stdout.strip(): raise RuntimeError("container lane is not empty")
    output.parent.mkdir(parents=True, exist_ok=True); output.mkdir()
    common = ["--rm", "--pull=never", "--platform", "linux/arm64", "--network", "none", "--read-only",
              "--cpus", "0.25", "--memory", "512m", "--pids-limit", "32", "--shm-size", "32m",
              "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
              "--mount", f"type=bind,source={REPO},target=/src,readonly",
              "--mount", f"type=bind,source={output},target=/out",
              "-e", f"OBSTAC_SOURCE_COMMIT={source_commit}", "-e", f"OBSTAC_IMAGE_ID={IMAGE}",
              "-e", f"OBSTAC_FREEZE_SHA256={freeze_sha}", "-e", "OBSTAC_CONSTRUCTION=0"]
    runner_cmd = ["docker", "run", *common, IMAGE, "python", str(EXP).replace(str(REPO), "/src") + "/runner.py"]
    auditor_cmd = ["docker", "run", *common, IMAGE, "python", str(EXP).replace(str(REPO), "/src") + "/audit.py"]
    started = time.time_ns(); formal = run(runner_cmd)
    (output / "formal.stdout.txt").write_text(formal.stdout); (output / "formal.stderr.txt").write_text(formal.stderr)
    auditor = run(auditor_cmd) if formal.returncode == 0 and (output / "raw.json").is_file() else None
    if auditor:
        (output / "audit.stdout.txt").write_text(auditor.stdout); (output / "audit.stderr.txt").write_text(auditor.stderr)
    execution = {"allocation": "needle-publication-orbstack-bind-5066-20260928-01", "formal_invocations": 1,
                 "runner_command": runner_cmd, "runner_exit": formal.returncode,
                 "auditor_command": auditor_cmd if auditor else None, "auditor_exit": auditor.returncode if auditor else None,
                 "image": inspected.stdout.strip(), "context": CONTEXT, "source_commit": source_commit,
                 "freeze_sha256": freeze_sha, "started_ns": started, "finished_ns": time.time_ns(),
                 "disposition": "AUDIT_REQUIRED" if not auditor else "AUDIT_COMPLETE"}
    (output / "execution.json").write_text(json.dumps(execution, sort_keys=True, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): {"bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
                for p in sorted(output.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"runner_exit": formal.returncode, "audit_exit": auditor.returncode if auditor else None,
                      "output": str(output)}, sort_keys=True))
    return 0 if auditor and auditor.returncode == 0 else 1


if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"preflight_error": type(exc).__name__, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise
