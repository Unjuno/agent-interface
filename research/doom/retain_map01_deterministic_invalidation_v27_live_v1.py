"""Retain the first frozen v27 deterministic composition allocation."""
import hashlib
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "results-local/doom/map01-deterministic-invalidation-v27-live-01"
TARGET = HERE / "results/map01-deterministic-invalidation-v27-live-01"


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
        "schema": "map01-deterministic-invalidation-v27-retention-v1",
        "allocation_id": "map01-deterministic-invalidation-v27-live-01",
        "source": str(SOURCE),
        "copy_contract": "byte-for-byte files from the first allocation; manifest excludes itself",
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
