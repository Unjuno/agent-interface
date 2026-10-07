#!/usr/bin/env python3
"""Write the pre-run source/runtime freeze; must run once into an empty raw/."""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "raw"


def command(args):
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {"argv": args, "exit": p.returncode, "output": p.stdout.strip()}


def main():
    if OUT.exists() and any(OUT.iterdir()):
        raise SystemExit("STOP_FREEZE_OUTPUT_NOT_EMPTY")
    files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(ROOT.rglob("*")) if p.is_file() and "raw" not in p.parts}
    repo = command(["git", "-C", str(ROOT.parents[2]), "rev-parse", "HEAD"])
    docker = command(["docker", "version", "--format", "{{.Client.Version}}/{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"])
    driver = command(["docker", "info", "--format", "{{.OSType}}/{{.Architecture}} {{.Driver}}"])
    image = command(["docker", "image", "inspect", "alpine@sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8", "--format", "{{.Id}} {{json .RepoDigests}}"])
    if any(x["exit"] for x in (repo, docker, driver, image)):
        raise SystemExit("STOP_FREEZE_RUNTIME_PROVENANCE")
    freeze = {"schema": "cow-7459-t0-freeze-v1", "repository_head": repo["output"],
              "docker": docker["output"], "driver": driver["output"],
              "pinned_image": image["output"], "files_sha256": files,
              "candidate_command": "python3 candidate.py", "audit_command": "python3 audit.py",
              "decision_gate": "METHOD_PASS_SCOPED only for exact clean deltas, unchanged base, and all planted uncertainty/effect cases refused; otherwise FAIL/HOLD/STOP per README."}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "freeze.json"
    path.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"freeze": str(path), "source_files": len(files), "head": repo["output"], "docker": docker["output"], "driver": driver["output"]}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FREEZE_STOP: {type(e).__name__}: {e}", file=sys.stderr)
        raise
