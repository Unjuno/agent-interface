"""Retain the only frozen natural-threat v26 allocation without transforming it."""
import hashlib
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "results-local/doom/map01-persistent-threat-v26-live-02"
TARGET = HERE / "results/map01-persistent-threat-v26-live-02"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if not (SOURCE / "report.json").is_file():
        raise FileNotFoundError(SOURCE / "report.json")
    if TARGET.exists():
        raise FileExistsError(TARGET)
    shutil.copytree(SOURCE, TARGET)
    files = []
    for path in sorted(TARGET.rglob("*")):
        if path.is_file() and path.name != "retention-manifest.json":
            files.append({"path": path.relative_to(TARGET).as_posix(),
                          "bytes": path.stat().st_size, "sha256": sha(path)})
    manifest = {
        "schema": "map01-persistent-threat-v26-retention-v1",
        "allocation_id": "map01-persistent-threat-v26-live-02",
        "source": str(SOURCE),
        "copy_contract": "byte-for-byte first allocation plus explicitly labelled post-run visual review; excludes manifest and post-copy audit",
        "excluded_derived_files": ["retention-manifest.json", "audit.json"],
        "total_files": len(files),
        "total_bytes": sum(row["bytes"] for row in files),
        "files": files,
    }
    (TARGET / "retention-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: manifest[key] for key in
                      ("allocation_id", "total_files", "total_bytes")}, indent=2))


if __name__ == "__main__":
    main()
