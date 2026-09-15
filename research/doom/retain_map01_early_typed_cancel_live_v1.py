"""Promote the first audited early-typed cancellation allocation unchanged."""
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
    audit = json.loads((SOURCE / "audit.json").read_text(encoding="utf-8"))
    if audit.get("passed") is not True:
        raise RuntimeError("source audit did not pass")
    shutil.copytree(SOURCE, TARGET)
    shutil.copy2(PREREG, TARGET / "preregistration.json")
    files = sorted(path for path in TARGET.rglob("*") if path.is_file())
    manifest = {str(path.relative_to(TARGET)).replace("\\", "/"): sha(path)
                for path in files}
    retention = {
        "passed": True,
        "decision": "RETAIN_MAP01_EARLY_TYPED_CANCEL_LIVE_V1",
        "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "source_audit_sha256": sha(SOURCE / "audit.json"),
        "manifest": manifest,
        "limits": "one controller-authored held-fire probe; no planner/model, task completion, gameplay gain or general human-tempo claim",
    }
    (TARGET / "retention.json").write_text(
        json.dumps(retention, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: retention[key] for key in
                      ("passed", "decision", "files", "bytes")}, indent=2))


if __name__ == "__main__":
    main()
