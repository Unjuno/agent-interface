"""Bind the two first-outcome retained directories with file-level hashes."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results"
ALLOCATIONS = ("map01-schema-v6-preflight-01", "map01-final-admission-v32-live-01")


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    for name in ALLOCATIONS:
        root = ROOT / name
        manifest = root / "retention-manifest.json"
        if manifest.exists(): raise FileExistsError(manifest)
        files = sorted(path for path in root.rglob("*") if path.is_file())
        rows = [{"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
                 "sha256": sha(path)} for path in files]
        value = {"schema": "map01-first-outcome-retention-v1", "allocation_id": name,
                 "source": f"results-local/doom/{name}", "files": rows,
                 "file_count": len(rows), "total_bytes": sum(row["bytes"] for row in rows),
                 "scope": "first frozen allocation copied without rerun; manifest excludes itself"}
        manifest.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"allocation": name, "files": len(rows), "bytes": value["total_bytes"]}))


if __name__ == "__main__": main()
