"""Retain the first audited client-wait v2 outcome without retry."""
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
SOURCE = REPO / "results-local/live_control/release-client-wait-live-02"
TARGET = HERE / "results/release-client-wait-live-02"
PREREG = HERE / "release_client_wait_live_v2_prereg.json"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    if TARGET.exists(): raise FileExistsError(TARGET)
    report, audit = read(SOURCE / "report.json"), read(SOURCE / "audit.json")
    if report["passed"] is not True or audit["passed"] is not True:
        raise RuntimeError("independently audited passing allocation required")
    shutil.copytree(SOURCE, TARGET); shutil.copy2(PREREG, TARGET / "preregistration.json")
    files = sorted(path for path in TARGET.rglob("*") if path.is_file())
    receipt = {"passed": True, "decision": "RETAIN_FIRST_OUTCOME_NO_RETRY",
        "allocation_passed": True, "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "manifest": {str(path.relative_to(TARGET)).replace("\\", "/"): sha(path)
                     for path in files},
        "metrics_ms": report["metrics_ms"],
        "scope": report["scope"]}
    (TARGET / "retention.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: receipt[key] for key in
        ("passed", "decision", "allocation_passed", "files", "bytes", "metrics_ms")},
        indent=2))

if __name__ == "__main__": main()
