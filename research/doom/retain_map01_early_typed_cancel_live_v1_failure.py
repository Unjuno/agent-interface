"""Retain the first frozen early-typed allocation failure unchanged."""
import hashlib
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "results-local/doom/map01-early-typed-cancel-live-01"
TARGET = HERE / "results/map01-early-typed-cancel-live-01"
PREREG = HERE / "map01_early_typed_cancel_live_v1_prereg.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if TARGET.exists():
        raise FileExistsError(TARGET)
    failure = json.loads((SOURCE / "failure.json").read_text(encoding="utf-8"))
    if (failure.get("allocation_passed") is not False or
            failure.get("wrapper_exit_code") != 1 or
            not all(failure.get("evidence", {}).values())):
        raise RuntimeError("complete audited first failure required")
    shutil.copytree(SOURCE, TARGET)
    shutil.copy2(PREREG, TARGET / "preregistration.json")
    files = sorted(path for path in TARGET.rglob("*") if path.is_file())
    manifest = {str(path.relative_to(TARGET)).replace("\\", "/"): sha(path)
                for path in files}
    retention = {
        "passed": True,
        "decision": "RETAIN_FIRST_FAILURE_NO_RETRY",
        "allocation_passed": False,
        "failure_class": failure["failure_class"],
        "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "source_failure_sha256": sha(SOURCE / "failure.json"),
        "manifest": manifest,
        "limits": failure["limits"],
    }
    (TARGET / "retention.json").write_text(
        json.dumps(retention, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: retention[key] for key in
                      ("passed", "decision", "allocation_passed",
                       "failure_class", "files", "bytes")}, indent=2))


if __name__ == "__main__":
    main()
