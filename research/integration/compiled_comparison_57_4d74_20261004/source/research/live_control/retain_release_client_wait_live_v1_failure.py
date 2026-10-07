"""Retain the first client-wait failure without retry."""
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
SOURCE = REPO / "results-local/live_control/release-client-wait-live-01"
TARGET = HERE / "results/release-client-wait-live-01"
PREREG = HERE / "release_client_wait_live_v1_prereg.json"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if TARGET.exists(): raise FileExistsError(TARGET)
    failure = json.loads((SOURCE / "failure.json").read_text(encoding="utf-8"))
    if failure["allocation_passed"] is not False or not all(failure["evidence"].values()):
        raise RuntimeError("audited failure required")
    shutil.copytree(SOURCE, TARGET); shutil.copy2(PREREG, TARGET / "preregistration.json")
    files = sorted(path for path in TARGET.rglob("*") if path.is_file())
    receipt = {"passed": True, "decision": "RETAIN_FIRST_FAILURE_NO_RETRY",
        "allocation_passed": False, "failure_class": failure["failure_class"],
        "files": len(files), "bytes": sum(path.stat().st_size for path in files),
        "manifest": {str(path.relative_to(TARGET)).replace("\\", "/"): sha(path)
                     for path in files}, "limits": failure["limits"]}
    (TARGET / "retention.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: receipt[key] for key in
        ("passed", "decision", "allocation_passed", "files", "bytes")}, indent=2))

if __name__ == "__main__": main()
