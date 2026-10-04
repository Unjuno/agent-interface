"""One-shot Windows-host paired runner for the frozen A04 suite comparison."""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
FORMAL = ROOT.parent / "m6389-a04-results-20261004"
BASE_MAIN = "8094af4631fc7bc5d92990e5151d5e89477ee39f"
IMAGE_TAG = "agent-interface/native-suite-wslc-a08:20261004"
IMAGE_ID = "sha256:1b4a8bd7c0fe372cc0cafa74af433b8ae1f73f1bee0f11a028f126b08b2c128a"
PYTHON = "/tmp/agent-interface-mcp-venv/bin/python"
WSL = Path(r"C:\Windows\System32\wsl.exe")
WSLC = Path(r"C:\Program Files\WSL\wslc.exe")
ORDERS = (("native", "wslc"), ("wslc", "native"), ("native", "wslc"))
EXPECTED_FILES = {
    "runtime/integration_checks/native.py": "6ea771ce3802a1d23eb98369b1dac80e153639d0e5c9c007ccab2f24d816e27d",
    "runtime/integration_checks/Dockerfile": "8a37c726cbb18b778397f4a7405a14ab533c5df7f442933a295e80a0579a892e",
    "research/live_control/requirements-native-mcp.txt": "4fe75062c5d424bbc86a8cd58c63ab19aeffe4f0a0e100022252c8032e12ee5b",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def wsl_path(path: Path) -> str:
    return f"/mnt/{path.drive[0].lower()}{path.as_posix().split(':', 1)[1]}"


def run(command: list[str], *, cwd: Path | None = None) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    tick = time.perf_counter()
    child = subprocess.run(command, cwd=cwd, capture_output=True, check=False)
    elapsed = time.perf_counter() - tick
    return {"command": command, "started_utc": started,
            "ended_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": elapsed, "exit_code": child.returncode,
            "stdout": child.stdout, "stderr": child.stderr}


def save_receipt(directory: Path, label: str, receipt: dict) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    stdout_path, stderr_path = directory / f"{label}.stdout.bin", directory / f"{label}.stderr.bin"
    stdout_path.write_bytes(receipt.pop("stdout"))
    receipt["stdout_path"] = stdout_path.name
    receipt["stdout_sha256"] = digest(stdout_path.read_bytes())
    stderr_path.write_bytes(receipt.pop("stderr"))
    receipt["stderr_path"] = stderr_path.name
    receipt["stderr_sha256"] = digest(stderr_path.read_bytes())
    return receipt


def append_event(stream, event: dict) -> None:
    stream.write(json.dumps(event, sort_keys=True) + "\n")
    stream.flush()


def wslc_gate(directory: Path) -> tuple[bool, dict]:
    idle = save_receipt(directory, "running-containers",
                        run([str(WSLC), "container", "ls", "--quiet"]))
    image_list = save_receipt(directory, "image-inventory",
                              run([str(WSLC), "images", "--digests", "--no-trunc"]))
    image_inspect = save_receipt(directory, "image-inspect",
                                 run([str(WSLC), "inspect", "-f", "json", IMAGE_TAG]))
    try:
        inspected = json.loads((directory / image_inspect["stdout_path"]).read_text(encoding="utf-8"))
        if isinstance(inspected, list):
            inspected = inspected[0]
        actual_id = inspected.get("Id")
    except (ValueError, IndexError, AttributeError):
        actual_id = None
    passed = (idle["exit_code"] == 0 and not (directory / idle["stdout_path"]).read_bytes().strip()
              and image_list["exit_code"] == 0
              and IMAGE_ID.encode() in (directory / image_list["stdout_path"]).read_bytes()
              and image_inspect["exit_code"] == 0 and actual_id == IMAGE_ID)
    return passed, {"running_containers": idle, "image_inventory": image_list,
                    "image_inspect": image_inspect, "observed_image_id": actual_id}


def main() -> int:
    if os.name != "nt":
        raise RuntimeError("measure.py must run from Windows Python")
    if FORMAL.exists():
        raise FileExistsError(f"formal output already exists: {FORMAL}")
    FORMAL.mkdir()
    journal = (FORMAL / "events.jsonl").open("x", encoding="utf-8", newline="\n")
    counts = {"native": [], "wslc": []}
    stop_reason = None
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=False)
        diff = subprocess.run(["git", "diff", "--quiet", BASE_MAIN, "HEAD", "--", "runtime/", "research/live_control/"], cwd=ROOT, check=False)
        source_mismatches = {name: {"expected": expected, "actual": digest((ROOT / name).read_bytes())}
                             for name, expected in EXPECTED_FILES.items()
                             if not (ROOT / name).is_file() or digest((ROOT / name).read_bytes()) != expected}
        source_gate = (head.returncode == 0 and status.returncode == 0 and not status.stdout.strip()
                       and diff.returncode == 0 and not source_mismatches)
        append_event(journal, {"type": "source_gate", "head": head.stdout.strip(),
                               "expected_base_main": BASE_MAIN, "clean": not status.stdout.strip(),
                               "source_diff_exit": diff.returncode, "source_mismatches": source_mismatches,
                               "passed": source_gate})
        if not source_gate:
            stop_reason = "STOP_FROZEN_SOURCE_MISMATCH"
        for pair, order in enumerate(ORDERS, 1):
            if stop_reason:
                break
            for arm in order:
                run_dir = FORMAL / f"pair-{pair:02d}" / arm
                run_dir.mkdir(parents=True)
                output_dir = run_dir / "results"
                if arm == "wslc":
                    passed, gate = wslc_gate(run_dir / "preflight")
                    append_event(journal, {"type": "wslc_preflight", "pair": pair,
                                           "gate": gate, "passed": passed})
                    if not passed:
                        stop_reason = "STOP_WSLC_GATE"
                        break
                    command = [str(WSLC), "run", "--rm", "--name", f"ai6389a04-p{pair}-{arm}",
                               "--pull", "never", "--network", "none", "--cpus", "1",
                               "--memory", "512M", "--user", "65534:65534",
                               "--volume", f"{ROOT}:/src:ro", "--volume", f"{run_dir}:/out:rw",
                               "--workdir", "/src", IMAGE_ID, "--output", "/out/results"]
                else:
                    command = [str(WSL), "-d", "Ubuntu", "--exec", PYTHON,
                               wsl_path(ROOT / "runtime/integration_checks/native.py"),
                               "--protocol-python", PYTHON, "--harness-python", PYTHON,
                               "--output", wsl_path(output_dir)]
                event = run(command)
                saved = save_receipt(run_dir, "launcher", event)
                counts[arm].append(saved["elapsed_seconds"])
                append_event(journal, {"type": "candidate", "allocation": "6389-wsl2-vs-wslc-native-suite-a04-20261004",
                                       "pair": pair, "arm": arm, "head": head.stdout.strip(),
                                       "receipt": saved})
                if saved["exit_code"] != 0 or not (output_dir / "result.json").is_file():
                    stop_reason = f"STOP_OR_FAIL_{arm.upper()}_CANDIDATE"
                    break
            if stop_reason:
                break
    finally:
        journal.close()
    complete = len(counts["native"]) == 3 and len(counts["wslc"]) == 3 and not stop_reason
    summary = {"allocation": "6389-wsl2-vs-wslc-native-suite-a04-20261004",
               "status": stop_reason or ("AWAITING_INDEPENDENT_AUDIT" if complete else "STOP_INCOMPLETE"),
               "native_invocations": len(counts["native"]), "wslc_invocations": len(counts["wslc"]),
               "native_seconds": counts["native"], "wslc_seconds": counts["wslc"],
               "retry_count": 0, "frozen_base_main": BASE_MAIN, "candidate_head": head.stdout.strip()}
    if complete:
        summary.update(native_median_seconds=statistics.median(counts["native"]),
                       wslc_median_seconds=statistics.median(counts["wslc"]))
    with (FORMAL / "summary.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(summary, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(summary, sort_keys=True))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
