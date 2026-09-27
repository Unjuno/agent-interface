"""Host-side freeze gates and exact one-shot Docker command receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "formal-output"
AUDIT_OUT = ROOT.parent / "audit-output"
RECEIPT_PATH = ROOT.parent / "invocation-receipt.json"
FREEZE_PATH = ROOT / "FREEZE.json"
IMAGE = "sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
EXPECTED_BROKER_SHA = "e44822269b921aa6327563b27e48a6d8ef4ebe35a182f50de541cf66fce6199c"
EXPECTED_MAIN = "b3af4e85f8bf7d41da5251b1728a6ddab34c3476"
EXPECTED_BROKER_BLOB = "5734f54f318db9ac5e96b2bed6f6bed105ac39ff"


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen_sources() -> dict[str, str]:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    expected = freeze.get("source", {}).get("sha256")
    if not isinstance(expected, dict) or not expected:
        raise ValueError("FREEZE.json has no source SHA-256 map")
    actual = {name: file_sha(ROOT / name) for name in sorted(expected)}
    if actual != expected:
        raise ValueError("frozen source SHA-256 mismatch")
    return actual


def require_fresh_paths(*paths: Path) -> None:
    for path in paths:
        if path.exists():
            raise FileExistsError(f"fresh evidence path must not exist: {path}")


def write_receipt_exclusive(path: Path, receipt: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


def preflight_command(source_repo: Path, source: Path, release: Path,
                      output: Path, audit_output: Path, receipt_path: Path,
                      command: list[str]) -> dict:
    """Validate all destinations and return a receipt without writing it."""
    require_fresh_paths(output, audit_output, receipt_path)
    return {
        "command": command,
        "resolved_repo": str(source_repo.resolve()),
        "resolved_study": str(source.resolve()),
        "resolved_output": str(output.resolve()),
        "resolved_audit_output": str(audit_output.resolve()),
        "resource_release": str(release.resolve()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--resource-release", type=Path, required=True)
    parser.add_argument("--observed-main", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    source_repo = args.source.resolve(strict=True)
    release = args.resource_release.resolve(strict=True)
    broker = source_repo / "host_model_ipc_broker_v1.py"
    source = ROOT.resolve(strict=True)
    if not (source / "runner.py").is_file() or not (source / "audit.py").is_file():
        raise FileNotFoundError("formal source bundle incomplete")
    frozen_source_hashes = verify_frozen_sources()
    if file_sha(broker) != EXPECTED_BROKER_SHA:
        raise ValueError("broker SHA-256 differs from frozen value")
    blob_sha = subprocess.run(["git", "hash-object", str(broker)], check=True,
                              capture_output=True, text=True).stdout.strip()
    if blob_sha != EXPECTED_BROKER_BLOB:
        raise ValueError("broker Git blob mismatch: " + blob_sha)
    if args.observed_main != EXPECTED_MAIN:
        raise ValueError("main advanced; re-read and re-freeze before invocation")
    require_fresh_paths(OUT, AUDIT_OUT, RECEIPT_PATH)
    image_id = subprocess.run(["docker", "--context", "desktop-linux", "image", "inspect", IMAGE,
                               "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"],
                              check=True, capture_output=True, text=True).stdout.strip()
    if image_id != IMAGE + " linux/amd64":
        raise ValueError("pinned image identity/platform mismatch: " + image_id)
    context = subprocess.run(["docker", "context", "show"], check=True,
                             capture_output=True, text=True).stdout.strip()
    if context != "desktop-linux":
        raise ValueError("expected Docker context desktop-linux, got: " + context)
    containers = subprocess.run(["docker", "--context", "desktop-linux", "ps", "--no-trunc", "--format",
                                 "{{.ID}} {{.Names}} {{.Status}}"],
                                check=True, capture_output=True, text=True).stdout
    ownership = json.loads(release.read_text(encoding="utf-8"))
    if ownership.get("issue") != 5074 or ownership.get("released") is not True:
        raise ValueError("explicit sibling Docker-slot release missing")
    if ownership.get("observed_running_containers") != [] or containers.strip():
        raise ValueError("Docker ownership/inventory is not clear")
    output = OUT.resolve()
    command = [
        "docker", "--context", "desktop-linux", "run", "--rm", "--pull=never", "--platform", "linux/amd64",
        "--network=none", "--read-only", "--cpus=0.25", "--memory=256m",
        "--pids-limit=32", "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
        "--tmpfs", "/tmp:rw,exec,nosuid,size=16m",
        "--mount", f"type=bind,src={source_repo},dst=/src,readonly",
        "--mount", f"type=bind,src={source},dst=/study,readonly",
        "--mount", f"type=bind,src={release},dst=/resource-release.json,readonly",
        "--mount", f"type=bind,src={ROOT.parent / 'invocation-receipt.json'},dst=/invocation-receipt.json,readonly",
        "--mount", f"type=bind,src={output},dst=/out",
        "-e", "EXPECTED_BROKER_SHA256=" + EXPECTED_BROKER_SHA,
        IMAGE, "python", "/study/runner.py",
    ]
    receipt = {
        "allocation": "broker-fake-child-timeout-start-20260928-01",
        "issue": 5074, "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "command": command, "resolved_repo": str(source_repo), "resolved_study": str(source),
        "resolved_output": str(output), "broker_git_blob": "5734f54f318db9ac5e96b2bed6f6bed105ac39ff",
        "broker_sha256": file_sha(broker), "image": image_id,
        "formal_source_sha256": frozen_source_hashes,
        "docker_inventory_before": containers.splitlines(),
        "ownership_release": ownership,
    }
    receipt["audit_command_template"] = [
        "docker", "--context", "desktop-linux", "run", "--rm", "--pull=never", "--platform", "linux/amd64",
        "--network=none", "--read-only", "--cpus=0.25", "--memory=256m",
        "--pids-limit=32", "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
        "--mount", f"type=bind,src={source},dst=/study,readonly",
        "--mount", f"type=bind,src={output},dst=/out,readonly",
        "--mount", f"type=bind,src={AUDIT_OUT.resolve()},dst=/audit-output",
        IMAGE, "python", "/study/audit.py",
    ]
    receipt.update(preflight_command(source_repo, source, release, OUT, AUDIT_OUT,
                                    RECEIPT_PATH, command))
    print(json.dumps({"preflight": "PASS", "receipt": str(RECEIPT_PATH),
                      "execute": args.execute, "command": command}, indent=2))
    if not args.execute:
        return 0
    write_receipt_exclusive(RECEIPT_PATH, receipt)
    OUT.mkdir(parents=True, exist_ok=False)
    AUDIT_OUT.mkdir(parents=True, exist_ok=False)
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        return completed.returncode
    return subprocess.run(receipt["audit_command_template"], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
