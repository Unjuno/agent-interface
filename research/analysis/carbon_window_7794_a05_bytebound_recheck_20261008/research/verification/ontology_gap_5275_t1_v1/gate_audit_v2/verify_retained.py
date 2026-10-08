"""One bounded maintenance verification; never execute the scientific runner."""
import argparse
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic_ns()
    cpu = min(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {cpu})
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    frozen = [SOURCE / n for n in ("audit_t1.py", "candidate.py", "corpus.json", "FORMAL-01.json", "FREEZE.json")]
    own = [HERE / n for n in ("audit_v2.py", "test_audit_v2.py", "verify_retained.py", "PLAN.md")]
    hashes_before = {str(p.relative_to(SOURCE)): digest(p) for p in frozen + own}
    receipt = {
        "kind": "retained_input_maintenance_verification_not_scientific_rerun",
        "status": "STARTED", "argv": sys.argv, "source_sha256": hashes_before,
        "environment": {"python": sys.version, "platform": platform.platform(), "executable": sys.executable,
            "affinity": sorted(os.sched_getaffinity(0)), "address_space_limit_bytes_per_process": resource.getrlimit(resource.RLIMIT_AS)[0],
            "cpu_time_limit_seconds_per_process": resource.getrlimit(resource.RLIMIT_CPU)[0], "nested_docker": False},
    }
    def save():
        (args.out / "RECEIPT.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    save()
    try:
        freeze = json.loads((HERE / "FREEZE.json").read_text())
        assert freeze["source_head"] == "bbf43bf7a569e9c79883756bef41cf7677e50239", "source head mismatch"
        assert freeze["source_sha256"] == hashes_before, "prelaunch source/raw hash mismatch"
        assert hashes_before["FORMAL-01.json"] == "ce1219edc12ed3526c0be90043bfe3428db3d36e42c6337e6f532e18ae2c72d6", "raw differs from reviewed first outcome"
        receipt["freeze_sha256"] = digest(HERE / "FREEZE.json")
        receipt["prelaunch_hash_gate"] = "PASS"
        save()
        raw = json.loads((SOURCE / "FORMAL-01.json").read_text())
        corpus = json.loads((SOURCE / "corpus.json").read_text())
        original = load_module("original_audit", SOURCE / "audit_t1.py")
        successor = load_module("audit_v2", HERE / "audit_v2.py")
        copies = {"original": copy.deepcopy(raw)}
        for name in ("empty_gates", "missing_gates", "extra_gate", "integer_gate", "flip_gate_and_verdict"):
            copies[name] = copy.deepcopy(raw)
        copies["empty_gates"]["gates"] = {}
        copies["missing_gates"].pop("gates")
        copies["extra_gate"]["gates"]["undeclared_gate"] = True
        copies["integer_gate"]["gates"]["all_cases_accounted"] = 1
        copies["flip_gate_and_verdict"]["gates"]["all_cases_accounted"] = False
        copies["flip_gate_and_verdict"]["disposition"] = "FAIL_LEXICAL_BOUNDARY"
        controls = []
        for name, payload in copies.items():
            old_stdout = io.StringIO()
            with contextlib.redirect_stdout(old_stdout):
                old_code = original.audit(payload)
            new_result = successor.audit_payload(payload, corpus, raw["source_identity"])
            controls.append({"name": name, "changed_from_original": payload != raw,
                "payload": payload, "original_exit": old_code, "original_result": json.loads(old_stdout.getvalue()),
                "successor_result": new_result})
            (args.out / "CONTROLS.json").write_text(json.dumps(controls, indent=2, allow_nan=False) + "\n")
            assert old_code == 0, "original auditor behavior differs from frozen finding: " + name
            assert new_result["integrity_pass"] is (name == "original"), name
        sys.path.insert(0, str(HERE))
        test_module = load_module("test_audit_v2", HERE / "test_audit_v2.py")
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_module))
        (args.out / "TESTS.txt").write_text(stream.getvalue())
        receipt["tests"] = {"run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped)}
        assert result.wasSuccessful(), "construction-control regression"
        argv = [sys.executable, "-B", str(HERE / "audit_v2.py"), str(SOURCE / "FORMAL-01.json")]
        completed = subprocess.run(argv, capture_output=True, text=True, timeout=5)
        (args.out / "CLI.stdout.json").write_text(completed.stdout)
        (args.out / "CLI.stderr.txt").write_text(completed.stderr)
        receipt["cli"] = {"argv": argv, "exit_code": completed.returncode}
        assert completed.returncode == 0, "retained-input CLI refused"
        assert json.loads(completed.stdout)["scientific_disposition"] == "PASS_SCOPED_LEXICAL_BOUNDARY"
        receipt["status"] = "PASS_GATE_INTEGRITY_CORRECTION_SCOPED"
    except Exception as exc:
        receipt["status"] = "FAIL_OR_STOP_RETAINED"
        receipt["exception"] = {"type": type(exc).__name__, "detail": str(exc)}
    finally:
        hashes_after = {str(p.relative_to(SOURCE)): digest(p) for p in frozen + own}
        receipt["source_unchanged"] = hashes_before == hashes_after
        if not receipt["source_unchanged"]:
            receipt["status"] = "FAIL_SOURCE_CHANGED"
        receipt["elapsed_ms"] = (time.monotonic_ns() - started) / 1_000_000
        receipt["self_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        receipt["children_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        receipt["output_sha256"] = {p.name: digest(p) for p in sorted(args.out.iterdir()) if p.is_file() and p.name != "RECEIPT.json"}
        save()
    print(json.dumps({"status": receipt["status"], "source_unchanged": receipt["source_unchanged"]}))
    return 0 if receipt["status"] == "PASS_GATE_INTEGRITY_CORRECTION_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
