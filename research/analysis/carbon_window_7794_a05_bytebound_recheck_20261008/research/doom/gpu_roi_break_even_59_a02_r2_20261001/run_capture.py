"""Run one frozen candidate and durably publish only a complete JSON result."""
from __future__ import annotations
import hashlib, json, os
from pathlib import Path
import subprocess, sys
ALLOCATION = "MAP01-ROI-BREAK-EVEN-59-GPU-20261001-02"
SCHEMA = "map01-roi-gpu-break-even-raw-v2"
ROOT = Path(__file__).resolve().parent
def _durable_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
def publish_candidate_stdout(stdout: bytes, stderr: bytes, returncode: int, output_dir: Path, expected_source_sha256: str) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    _durable_write(output_dir / "candidate.stderr.bin", stderr)
    partial = output_dir / "candidate.stdout.partial"
    if partial.exists():
        return {"allocation": ALLOCATION, "candidate_returncode": returncode, "raw_published": False, "stop_reason": "partial_path_already_exists"}
    _durable_write(partial, stdout)
    result = {"allocation": ALLOCATION, "candidate_returncode": returncode, "raw_published": False, "stop_reason": None}
    if returncode not in (0, 1):
        result["stop_reason"] = f"candidate_exit_{returncode}"
        return result
    try:
        raw = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        result["stop_reason"] = "stdout_not_complete_utf8_json"
        return result
    if not isinstance(raw, dict):
        result["stop_reason"] = "raw_root_not_object"
        return result
    checks = {"schema": raw.get("schema") == SCHEMA, "allocation": raw.get("allocation") == ALLOCATION, "source_sha256": raw.get("source_sha256") == expected_source_sha256}
    parity = raw.get("parity")
    checks["candidate_status"] = (parity is True and returncode == 0 and raw.get("status") == "DIAGNOSTIC_COMPLETE") or (parity is False and returncode == 1 and raw.get("status") == "FAIL_GPU_CPU_PARITY")
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        result["stop_reason"] = ",".join(failed)
        return result
    raw_path = output_dir / "candidate.json"
    if raw_path.exists() or (output_dir / "publication_receipt.json").exists():
        result["stop_reason"] = "output_path_already_exists"
        return result
    os.replace(partial, raw_path)
    raw_sha256 = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    receipt = {"allocation": ALLOCATION, "candidate_returncode": returncode, "raw_sha256": raw_sha256, "stderr_sha256": hashlib.sha256(stderr).hexdigest(), "raw_bytes": raw_path.stat().st_size, "durable_publication": True}
    _durable_write(output_dir / "publication_receipt.json", json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    result.update({"raw_published": True, "raw_sha256": raw_sha256, "raw_bytes": receipt["raw_bytes"]})
    return result
def main() -> int:
    benchmark = ROOT / "benchmark.py"
    output_dir = ROOT / "raw"
    if any((output_dir / name).exists() for name in ("candidate.json", "candidate.stdout.partial", "publication_receipt.json")):
        print(json.dumps({"status": "STOP_OUTPUT_PATH_ALREADY_EXISTS"}, sort_keys=True))
        return 82
    source_sha256 = hashlib.sha256(benchmark.read_bytes()).hexdigest()
    try:
        completed = subprocess.run([sys.executable, "-B", str(benchmark)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as exc:
        print(json.dumps({"status": "STOP_CANDIDATE_NOT_STARTED", "error": type(exc).__name__}, sort_keys=True))
        return 80
    result = publish_candidate_stdout(completed.stdout, completed.stderr, completed.returncode, output_dir, source_sha256)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["raw_published"] else 81
if __name__ == "__main__":
    raise SystemExit(main())
