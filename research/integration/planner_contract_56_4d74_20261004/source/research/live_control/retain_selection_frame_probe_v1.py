"""Retain the first frozen exact-frame selection probe comparison."""
import hashlib
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "results-local/live_control/selection-frame-probe-01"
TARGET = HERE / "results/selection-frame-probe-01"
PREREG = HERE / "selection_frame_probe_v1_prereg.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    if TARGET.exists():
        raise FileExistsError(TARGET)
    report, audit = read(SOURCE/"report.json"), read(SOURCE/"audit.json")
    if report["passed"] is not True or audit["passed"] is not True:
        raise RuntimeError("audited first pass required")
    shutil.copytree(SOURCE, TARGET)
    shutil.copy2(PREREG, TARGET/"preregistration.json")
    files = sorted(path for path in TARGET.rglob("*") if path.is_file())
    receipt = {
        "passed": True,
        "decision": "RETAIN_FIRST_OUTCOME_NO_RETRY",
        "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "metrics": report["metrics"],
        "manifest": {str(path.relative_to(TARGET)).replace("\\", "/"): sha(path)
                     for path in files},
        "scope": report["scope"],
    }
    (TARGET/"retention.json").write_text(json.dumps(receipt, indent=2)+"\n",
                                         encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
