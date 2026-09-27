"""Frozen shell-free container launcher for one isolated audit process."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

WHEELS = {
    "attrs-26.1.0-py3-none-any.whl": "c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309",
    "jsonschema-4.25.1-py3-none-any.whl": "3fba0169e345c7175110351d456342c364814cfcf3b964ba4587f22915230a63",
    "jsonschema_specifications-2025.9.1-py3-none-any.whl": "98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe",
    "referencing-0.37.0-py3-none-any.whl": "381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231",
    "rpds_py-2026.6.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl": "ecabd69db66de867690f9797f2f8fa27ba501bbc24540cbdbdc649cd15888ba6",
    "typing_extensions-4.16.0-py3-none-any.whl": "481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8",
}

def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--preflight", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise SystemExit("refusing to use nonempty output directory")
    wheels = Path("/wheelhouse")
    observed = {p.name: sha(p) for p in wheels.glob("*.whl")}
    if observed != WHEELS:
        raise SystemExit("wheelhouse SHA-256 mismatch")
    Path("/tmp/site").mkdir(exist_ok=True)
    pip = subprocess.run([sys.executable, "-B", "-m", "pip", "install", "--no-index",
                          "--no-cache-dir", "--find-links=/wheelhouse", "--target=/tmp/site",
                          "jsonschema==4.25.1"], capture_output=True, text=True)
    (out / "pip.stdout").write_text(pip.stdout, encoding="utf-8")
    (out / "pip.stderr").write_text(pip.stderr, encoding="utf-8")
    (out / "pip.exit").write_text(str(pip.returncode) + "\n", encoding="ascii")
    if pip.returncode:
        print("pinned offline dependency install failed", file=sys.stderr)
        return pip.returncode
    env = os.environ.copy()
    env["PYTHONPATH"] = "/tmp/site"
    if a.preflight:
        probe = subprocess.run([sys.executable, "-B", "-c",
                                "import importlib.metadata,jsonschema,rpds; print(importlib.metadata.version('jsonschema'), rpds.__file__)"]
                               , env=env, capture_output=True, text=True)
        (out / "preflight.stdout").write_text(probe.stdout, encoding="utf-8")
        (out / "preflight.stderr").write_text(probe.stderr, encoding="utf-8")
        (out / "preflight.exit").write_text(str(probe.returncode) + "\n", encoding="ascii")
        print(json.dumps({"preflight": True, "returncode": probe.returncode}))
        return probe.returncode
    script = Path("/study") / a.script
    run = subprocess.run([sys.executable, "-B", str(script)], env=env, capture_output=True, text=True)
    (out / "audit.stdout").write_text(run.stdout, encoding="utf-8")
    (out / "audit.stderr").write_text(run.stderr, encoding="utf-8")
    (out / "audit.exit").write_text(str(run.returncode) + "\n", encoding="ascii")
    print(json.dumps({"script": a.script, "returncode": run.returncode,
                      "stdout_bytes": len(run.stdout.encode()), "stderr_bytes": len(run.stderr.encode())}))
    return run.returncode

if __name__ == "__main__":
    raise SystemExit(main())
