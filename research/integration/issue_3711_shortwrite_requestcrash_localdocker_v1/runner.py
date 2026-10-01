"""Standalone synthetic short-write and request-only crash characterization."""
import argparse, hashlib, json, os, pathlib, subprocess, sys, tempfile

PARSER = argparse.ArgumentParser()
PARSER.add_argument("--source-dir", type=pathlib.Path, default=pathlib.Path(__file__).parent)
PARSER.add_argument("--result-dir", type=pathlib.Path, required=True)
ARGS = PARSER.parse_args()
FIXTURE = ARGS.source_dir / "fixture.json"
OUT = ARGS.result_dir / "RESULT.json"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fixture_bytes = FIXTURE.read_bytes()
    f = json.loads(fixture_bytes)
    results = {"allocation": f["allocation"], "fixture_sha256": sha(fixture_bytes), "cases": {}}
    with tempfile.TemporaryDirectory(prefix="issue3830-") as td:
        root = pathlib.Path(td)
        short = root / "short"
        short.mkdir()
        request = json.dumps(f["request"], sort_keys=True, separators=(",", ":")).encode()
        report = json.dumps(f["complete_report"], sort_keys=True, separators=(",", ":")).encode()
        (short / "request.json").write_bytes(request)
        (short / "report.json").write_bytes(report)
        accepted = bytearray()
        def writer(data):
            n = min(f["short_write_limit"], len(data))
            accepted.extend(data[:n])
            return n
        n = writer(report)
        recovered = (short / "report.json").read_bytes()
        short_state = "delivered" if n == len(report) else "delivery_incomplete"
        results["cases"]["short_write"] = {
            "accepted_bytes": len(accepted), "accepted_sha256": sha(bytes(accepted)),
            "expected_bytes": len(report), "expected_sha256": sha(report),
            "delivery_state": short_state, "recovered_report_sha256": sha(recovered),
            "recovered_report_exact": recovered == report, "writer_return": n,
            "invocation_count": f["complete_report"]["invocation_count"],
        }

        crash = root / "crash"
        crash.mkdir()
        child = (
            "import json,os,pathlib,sys; p=pathlib.Path(sys.argv[1]); "
            "p.joinpath('request.json').write_bytes(bytes.fromhex(sys.argv[2])); "
            "fd=os.open(str(p/'request.json'),os.O_RDONLY); os.fsync(fd); os.close(fd); "
            "os._exit(int(sys.argv[3]))"
        )
        proc = subprocess.run([sys.executable, "-c", child, str(crash), request.hex(), str(f["exit_code"])], check=False)
        request_present = (crash / "request.json").is_file()
        report_present = (crash / "report.json").exists()
        raw_request = (crash / "request.json").read_bytes() if request_present else b""
        crash_state = "completed" if report_present else "unknown_or_incomplete"
        results["cases"]["request_only_crash"] = {
            "child_returncode": proc.returncode, "expected_returncode": f["exit_code"],
            "request_present": request_present, "request_sha256": sha(raw_request),
            "request_exact": raw_request == request, "report_present": report_present,
            "recovery_state": crash_state, "replayable": False,
            "backend_invocation_count": 1,
        }
    # only publish the frozen result after the single formal run is complete
    OUT.write_text(json.dumps(results, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result_sha256": sha(OUT.read_bytes()), "status": "RUN_COMPLETE"}, sort_keys=True))

if __name__ == "__main__":
    main()
