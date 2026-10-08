"""Check retained v38 files and rerun the frozen mechanics audit on the copy."""
import hashlib
import json
from pathlib import Path

from audit_map01_v38_integrated_live_v1 import PLAN, read, result


ROOT = Path(__file__).resolve().parent / "results/map01-v38-integrated-threat-live-01"


def main():
    manifest = read(ROOT / "retention-manifest.json")
    assert manifest["allocation_id"] == ROOT.name
    assert manifest["file_count"] == len(manifest["files"])
    assert manifest["total_bytes"] == sum(row["bytes"] for row in manifest["files"])
    listed = {row["path"] for row in manifest["files"]}
    actual = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*")
              if path.is_file() and path.name != "retention-manifest.json"}
    assert listed == actual
    for row in manifest["files"]:
        path = ROOT / row["path"]
        assert path.stat().st_size == row["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
    audited = result(read(PLAN), ROOT)
    assert audited["formal_pass"] is True
    assert audited == read(ROOT / "audit.json")
    print(json.dumps({"passed": True, "file_count": manifest["file_count"],
                      "total_bytes": manifest["total_bytes"],
                      "decision": audited["decision"],
                      "integrated_running_path_exposed": audited["integrated_running_path_exposed"],
                      "dynamic_revocation_exposed": audited["dynamic_revocation_exposed"]}, indent=2))


if __name__ == "__main__":
    main()
