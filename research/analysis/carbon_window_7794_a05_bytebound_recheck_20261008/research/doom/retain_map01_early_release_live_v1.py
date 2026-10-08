"""Retain the first passing two-phase release allocation."""
import hashlib
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "results-local/doom/map01-early-release-live-01"
TARGET = HERE / "results/map01-early-release-live-01"
PREREG = HERE / "map01_early_release_live_v1_prereg.json"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if TARGET.exists(): raise FileExistsError(TARGET)
    report = json.loads((SOURCE / "report.json").read_text(encoding="utf-8"))
    audit = json.loads((SOURCE / "audit.json").read_text(encoding="utf-8"))
    if report.get("passed") is not True or audit.get("passed") is not True:
        raise RuntimeError("passing report and independent audit required")
    shutil.copytree(SOURCE, TARGET)
    shutil.copy2(PREREG, TARGET / "preregistration.json")
    files = sorted(path for path in TARGET.rglob("*") if path.is_file())
    manifest = {str(path.relative_to(TARGET)).replace("\\", "/"): sha(path)
                for path in files}
    receipt = {"passed": True, "decision": "RETAIN_FIRST_PASS_NO_RETRY",
        "allocation_passed": True, "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "manifest": manifest,
        "scope": report["scope"]}
    (TARGET / "retention.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: receipt[key] for key in
        ("passed", "decision", "files", "bytes")}, indent=2))


if __name__ == "__main__": main()
