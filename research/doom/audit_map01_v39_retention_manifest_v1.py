"""Verify first-outcome retained files and the versioned audit result."""
import hashlib
import json
from pathlib import Path

from audit_map01_v39_coast_liveness_retained_v2 import ROOT, exact_observation_artifacts


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    value = read(ROOT / "retention-manifest.json")
    assert value["allocation_id"] == ROOT.name
    assert value["file_count"] == len(value["files"])
    assert value["total_bytes"] == sum(row["bytes"] for row in value["files"])
    listed = {row["path"] for row in value["files"]}
    actual = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*")
              if path.is_file() and path.name != "retention-manifest.json"}
    assert listed == actual
    for row in value["files"]:
        path = ROOT / row["path"]
        assert path.stat().st_size == row["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
    original = read(ROOT / "audit.json")
    corrected = read(ROOT / "audit-v2.json")
    assert original["formal_pass"] is False and original["checks"]["exact_frames"] is False
    assert corrected["formal_pass"] is True and corrected["original_audit_formal_pass"] is False
    assert corrected["exact_observation_artifacts"] == exact_observation_artifacts(ROOT)
    assert corrected["coast_completed_after_damage"] is True
    assert corrected["dynamic_revocation_exposed"] is True
    print(json.dumps({"passed": True, "files": value["file_count"],
                      "bytes": value["total_bytes"],
                      "original_audit_formal_pass": False,
                      "retained_v2_formal_pass": True}, indent=2))


if __name__ == "__main__":
    main()
