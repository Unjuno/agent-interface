"""Stage retained bytes and run the independent audit in isolated OrbStack."""
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
IMAGE = "issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51"


def main():
    formal, audit = ROOT / "formal", ROOT / "audit"
    out = audit / "out"
    if audit.exists():
        raise SystemExit("STOP_AUDIT_DIR_EXISTS")
    audit.mkdir()
    out.mkdir()
    for name in ("FREEZE.json", "PREREGISTRATION.md"):
        shutil.copy2(ROOT / name, audit / name)
    for name in ("manifest.json", "probe.py", "bridge.py", "audit.py", "launcher.py", "audit_launcher.py"):
        shutil.copy2(SRC / name, audit / name)
    for source, target in ((formal / "output/RESULT.json", audit / "RESULT.json"),
                           (formal / "output/image.png", audit / "image.png"),
                           (formal / "output/BRIDGE_SUMMARY.json", audit / "BRIDGE_SUMMARY.json"),
                           (formal / "exchange/request-01.json", audit / "request-01.json"),
                           (formal / "exchange/response-01.json", audit / "response-01.json")):
        shutil.copy2(source, target)
    freeze = json.loads((audit / "FREEZE.json").read_text())
    image_id = subprocess.check_output(["docker", "--context", "orbstack", "image", "inspect", IMAGE, "--format", "{{.Id}}"], text=True).strip()
    if image_id != freeze["image_id"]:
        raise SystemExit("STOP_AUDIT_IMAGE_MISMATCH")
    command = ["docker", "--context", "orbstack", "run", "--rm", "--pull=never", "--platform", "linux/arm64",
               "--network", "none", "--read-only", "--workdir", "/tmp", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
               "--pids-limit", "16", "--memory", "256m", "--cpus", "1", "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges", "-v", f"{SRC}:/task:ro", "-v", f"{audit}:/audit:ro",
               "-v", f"{out}:/out:rw", IMAGE, "python", "/task/audit.py"]
    result = subprocess.run(command, check=False, text=True)
    print(json.dumps({"docker_context": "orbstack", "audit_exit_code": result.returncode,
                      "audit_path": str(out / "AUDIT.json")}, sort_keys=True))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
