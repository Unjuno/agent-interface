"""Retain the first frozen golden desktop app-server v2 failure."""
import hashlib
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "results-local/golden-desktop-app-server-v2-live-01"
TARGET = HERE / "results/golden-desktop-app-server-v2-live-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if not (SOURCE / "failure.json").is_file():
        raise FileNotFoundError(SOURCE / "failure.json")
    if TARGET.exists():
        raise FileExistsError(TARGET)
    shutil.copytree(SOURCE, TARGET)
    files = []
    for path in sorted(TARGET.rglob("*")):
        if path.is_file() and path.name != "retention-manifest.json":
            files.append({"path": path.relative_to(TARGET).as_posix(),
                          "bytes": path.stat().st_size, "sha256": sha(path)})
    manifest = {
        "schema": "golden-desktop-app-server-v2-failure-retention-v1",
        "allocation_id": "golden-desktop-app-server-v2-live-01",
        "copy_contract": "byte-for-byte first allocation; manifest excludes itself",
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
