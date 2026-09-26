"""Finite, display-free engineering comparison. Never calls a native backend."""
from __future__ import annotations
import argparse
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time


def digest(data):
    return hashlib.sha256(data).hexdigest()


def invoke(argv, cwd):
    env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY", "PYTHONPATH")}
    start = time.monotonic_ns()
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=25)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        return {"argv": argv, "pid": process.pid, "exit": process.returncode,
                "stdout": stdout.decode(), "stderr": stderr.decode(), "timeout": True,
                "start_ns": start, "end_ns": time.monotonic_ns()}
    return {"argv": argv, "pid": process.pid, "exit": process.returncode,
            "stdout": stdout.decode(), "stderr": stderr.decode(), "timeout": False,
            "start_ns": start, "end_ns": time.monotonic_ns()}


def worker(root, cases_path, out):
    sys.path.insert(0, str(root))
    from runtime.core_v1 import contract
    from runtime.core_v1.sequence import expand_key_repeats, expand_text_gaps
    inspect = runpy.run_path(str(root / "runtime/cli_v1/validate_program.py"))["inspect_program"]
    build = runpy.run_path(str(root / "runtime/distribution_v2/build_validator.py"))["build"]
    archive = out / "validator.pyz"
    build(root, archive, out / "BUILD.json", out / "validator.sha256")
    supported = contract.capability_manifest("test", "linux", "inert", contract.KNOWN_CAPABILITIES,
                                            frames=sorted(contract.COORDINATE_FRAMES))
    with (out / "rows.jsonl").open("x") as records:
        for case in json.loads(cases_path.read_text()):
            raw = case["input"].encode()
            path = out / "input.json"
            path.write_bytes(raw)
            program = json.loads(raw)
            expanded = json.loads(raw)
            if case["mode"] == "repeat":
                expanded["ops"] = expand_key_repeats(expanded["ops"], max_ops=128)
            elif case["mode"] == "gap":
                expanded["ops"], _ = expand_text_gaps(expanded["ops"])
            before = json.dumps(expanded, sort_keys=True)
            try:
                contract.validate_program(expanded)
                core = {"kind": "valid", "caps": list(contract.required_capabilities(expanded))}
            except (TypeError, contract.ContractError) as error:
                core = {"kind": type(error).__name__, "detail": str(error),
                        "index": getattr(error, "operation_index", None)}
            try:
                admitted = contract.admit_program(expanded, supported, now_ns=10,
                                                   current_observation_seq=1, current_binding_revision=1)
                admission = dataclasses.asdict(admitted)
            except TypeError as error:
                admission = {"exception": "TypeError", "detail": str(error)}
            report = inspect(program)
            direct_unchanged = json.dumps(program, sort_keys=True) == json.dumps(json.loads(raw), sort_keys=True)
            cli = invoke([sys.executable, "-I", "-S", "-B", str(archive), "--program", str(path)], out)
            row = {"id": case["id"], "input_sha256": digest(raw), "core": core,
                   "admission": admission, "static": report, "cli": cli,
                   "input_unchanged": path.read_bytes() == raw and direct_unchanged,
                   "expanded_unchanged": json.dumps(expanded, sort_keys=True) == before}
            records.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            records.flush()
            if cli["timeout"]:
                raise RuntimeError("CLI deadline exceeded; retain partial rows")
    (out / "input.json").unlink()
    print(json.dumps({"rows": len(json.loads(cases_path.read_text())),
                      "imported_native": [m for m in sys.modules if m.startswith(("Xlib", "tkinter", "runtime.backends"))],
                      "archive_sha256": digest(archive.read_bytes())}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    paths = [Path(p).resolve() for p in args.paths]
    if args.worker:
        worker(*paths)
        return
    baseline, candidate, out = paths
    freeze = json.loads(Path(__file__).with_name("FREEZE.json").read_text())
    for name, expected in freeze["files"].items():
        if digest((Path(__file__).parent.parent / name).read_bytes()) != expected:
            raise RuntimeError("source freeze mismatch: " + name)
    out.mkdir()
    cases = Path(__file__).with_name("cases.json")
    receipts = []
    for arm, root in (("baseline", baseline), ("candidate", candidate)):
        destination = out / arm
        destination.mkdir()
        receipt = invoke([sys.executable, "-S", "-B", str(Path(__file__).resolve()),
                          "--worker", str(root), str(cases), str(destination)], out)
        receipt["arm"] = arm
        receipts.append(receipt)
        (out / "EXECUTION.json").write_text(json.dumps(receipts, indent=2) + "\n")
        if receipt["exit"] != 0 or receipt["timeout"]:
            raise RuntimeError("worker failed; retain first outcome")
    print(json.dumps({"status": "complete", "arms": 2, "cases_per_arm": 123}))


if __name__ == "__main__":
    main()
