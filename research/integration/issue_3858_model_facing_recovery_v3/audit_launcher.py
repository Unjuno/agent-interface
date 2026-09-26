"""Copy retained formal bytes and invoke the isolated independent auditor."""
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
IMAGE = "issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51"


def main():
    formal, audit = ROOT / "formal", ROOT / "audit"
    inputs, output = audit / "input", audit / "output"
    if audit.exists():
        raise SystemExit("STOP_AUDIT_PATH_EXISTS")
    inputs.mkdir(parents=True)
    output.mkdir()
    for name in ("FREEZE.json", "PREREGISTRATION.md", "manifest.json", "policy.py", "runner.py", "host_bridge.py", "audit.py", "launcher.py", "audit_launcher.py"):
        shutil.copy2(ROOT / name, inputs / name)
    shutil.copy2(formal / "output/RESULT.json", inputs / "RESULT.json")
    shutil.copy2(formal / "output/BRIDGE_SUMMARY.json", inputs / "BRIDGE_SUMMARY.json")
    shutil.copytree(formal / "output/images", inputs / "images")
    shutil.copytree(formal / "exchange", inputs / "exchange", ignore=shutil.ignore_patterns("DONE", "BRIDGE_SUMMARY.json"))
    freeze = json.loads((inputs / "FREEZE.json").read_text())
    image_info = subprocess.check_output(["docker", "--context", "orbstack", "image", "inspect", IMAGE,
                                          "--format", "{{.Id}}"], text=True).strip()
    if image_info != freeze["image_id"]:
        raise SystemExit("STOP_AUDIT_IMAGE_MISMATCH")
    cmd = ["docker", "--context", "orbstack", "run", "--rm", "--pull=never", "--platform", "linux/arm64",
           "--network", "none", "--read-only", "--workdir", "/tmp", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
           "--pids-limit", "16", "--memory", "256m", "--cpus", "1", "--cap-drop", "ALL",
           "--security-opt", "no-new-privileges", "-v", f"{inputs}:/audit:ro", "-v", f"{output}:/out:rw",
           IMAGE, "python", "/audit/audit.py"]
    result = subprocess.run(cmd, check=False)
    print(json.dumps({"audit_exit_code": result.returncode, "audit_path": str(output / "AUDIT.json"),
                      "docker_context": "orbstack"}, sort_keys=True))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
