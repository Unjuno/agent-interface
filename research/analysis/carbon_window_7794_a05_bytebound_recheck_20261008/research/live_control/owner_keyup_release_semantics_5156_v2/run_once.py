"""Run the frozen host-only receipt-construction suite once and retain outputs."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_once.py PACKAGE_ROOT OUTPUT_DIRECTORY")
    root, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    if out.exists():
        raise SystemExit(f"STOP_OUTPUT_EXISTS: {out}")
    if out.relative_to(root).as_posix() != freeze["output_path"]:
        raise SystemExit("STOP_OUTPUT_PATH_MISMATCH")
    for name, expected in freeze["source_sha256"].items():
        if digest(HERE / name) != expected:
            raise SystemExit(f"STOP_SOURCE_HASH: {name}")
    out.mkdir(parents=True, exist_ok=False)
    started = time.time_ns()
    commands = {
        "tests": [sys.executable, "-B", str(HERE / "test_release_protocol_v2.py")],
        "audit": [sys.executable, "-B", str(HERE / "audit_protocol_v2.py")],
    }
    outcomes = {}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=HERE, capture_output=True, text=True)
        (out / f"{name}.stdout.txt").write_text(result.stdout, encoding="utf-8")
        (out / f"{name}.stderr.txt").write_text(result.stderr, encoding="utf-8")
        (out / f"{name}.exit-code").write_text(f"{result.returncode}\n", encoding="ascii")
        outcomes[name] = result.returncode
    receipt = {
        "schema": "owner-keyup-release-semantics-host-run-v1",
        "allocation": freeze["allocation"],
        "status": "PASS_RELEASE_EVENT_CLASSIFICATION_CONSTRUCTION_SCOPED"
                  if all(code == 0 for code in outcomes.values()) else "FAIL_CONSTRUCTION",
        "input_main_commit": freeze["input_main_commit"],
        "runtime": sys.version,
        "platform": sys.platform,
        "commands": commands,
        "exit_codes": outcomes,
        "started_ns": started,
        "ended_ns": time.time_ns(),
        "docker_used": False,
        "x11_or_input_used": False,
        "model_or_provider_used": False,
        "authority_grants": 0,
    }
    (out / "execution.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
