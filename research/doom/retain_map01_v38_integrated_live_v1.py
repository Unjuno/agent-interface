"""Hash the copied first v38 integrated MAP01 outcome file by file."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "results/map01-v38-integrated-threat-live-01"


def main():
    manifest = ROOT / "retention-manifest.json"
    if manifest.exists():
        raise FileExistsError(manifest)
    files = sorted(path for path in ROOT.rglob("*") if path.is_file())
    rows = [{"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in files]
    value = {"schema": "map01-v38-first-outcome-retention-v1",
             "allocation_id": ROOT.name,
             "source": "results-local/doom/map01-v38-integrated-threat-live-01",
             "files": rows, "file_count": len(rows),
             "total_bytes": sum(row["bytes"] for row in rows),
             "scope": "copied first frozen allocation without rerun; manifest excludes itself"}
    manifest.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"files": value["file_count"], "bytes": value["total_bytes"]}))


if __name__ == "__main__":
    main()
