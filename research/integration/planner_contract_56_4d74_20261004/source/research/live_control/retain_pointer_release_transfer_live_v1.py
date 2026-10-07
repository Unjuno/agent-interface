"""Manifest the first frozen pointer-transfer result in place."""
import hashlib
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/pointer-release-transfer-live-01"
PREREG = HERE / "pointer_release_transfer_live_v1_prereg.json"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    target = ROOT / "retention.json"
    if target.exists(): raise FileExistsError(target)
    report = json.loads((ROOT / "report.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "audit.json").read_text(encoding="utf-8"))
    if report.get("passed") is not True or audit.get("passed") is not True:
        raise RuntimeError("first passing report and audit required")
    shutil.copy2(PREREG, ROOT / "preregistration.json")
    files = sorted(path for path in ROOT.iterdir() if path.is_file())
    receipt = {"passed": True, "decision": "RETAIN_FIRST_PASS_NO_RETRY",
        "allocation_passed": True, "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "manifest": {path.name: sha(path) for path in files},
        "scope": report["scope"]}
    target.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: receipt[key] for key in
        ("passed", "decision", "files", "bytes")}, indent=2))


if __name__ == "__main__": main()
