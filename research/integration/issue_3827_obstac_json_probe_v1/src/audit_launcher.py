"""Stage immutable formal bytes and invoke the independent auditor in OrbStack."""
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parents[1]
SRC = HERE / "src"
IMAGE = "issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51"


def main():
    formal = HERE / "formal"
    audit = HERE / "audit"
    out = audit / "out"
    if audit.exists():
        raise SystemExit("STOP_AUDIT_DIRECTORY_ALREADY_EXISTS")
    audit.mkdir()
    out.mkdir()
    for name in ("FREEZE.json", "PREREGISTRATION.md"):
        shutil.copy2(HERE / name, audit / name)
    for name in ("manifest.json", "runner.py", "host_bridge.py", "audit.py", "launcher.py", "audit_launcher.py"):
        shutil.copy2(SRC / name, audit / name)
    shutil.copy2(formal / "output/RESULT.json", audit / "RESULT.json")
    shutil.copy2(formal / "output/image.png", audit / "image.png")
    shutil.copy2(formal / "output/BRIDGE_SUMMARY.json", audit / "BRIDGE_SUMMARY.json")
    shutil.copy2(formal / "exchange/request-01.json", audit / "request-01.json")
    shutil.copy2(formal / "exchange/response-01.json", audit / "response-01.json")
    image_id = subprocess.check_output(["docker", "--context", "orbstack", "image", "inspect", IMAGE, "--format", "{{.Id}}"], text=True).strip()
    freeze = json.loads((audit / "FREEZE.json").read_text())
    if image_id != freeze["image_id"]:
        raise SystemExit("STOP_AUDIT_IMAGE_ID_MISMATCH")
    command = ["docker", "--context", "orbstack", "run", "--rm", "--pull=never", "--platform", "linux/arm64",
               "--network", "none", "--read-only", "--workdir", "/tmp", "--tmpfs", "/tmp:rw,nosuid,noexec,size=16m",
               "--pids-limit", "16", "--memory", "256m", "--cpus", "1", "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges", "-v", f"{SRC}:/task:ro", "-v", f"{audit}:/audit:ro",
               "-v", f"{out}:/out:rw", IMAGE, "python", "/task/audit.py"]
    result = subprocess.run(command, check=False, text=True)
    print(json.dumps({"docker_context": "orbstack", "audit_exit_code": result.returncode,
                      "audit_path": str(out / "AUDIT.json")}, sort_keys=True))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
