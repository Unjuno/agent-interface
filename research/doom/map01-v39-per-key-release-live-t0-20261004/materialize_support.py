"""Create a deterministic, hash-manifested Python support snapshot from HEAD."""
import argparse
import gzip
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PREFIXES = (
    "research/observation_gating/",
    "research/observation_tiles/",
    "research/real_apps_v1/",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=ROOT, text=True
    ).splitlines()
    selected = [
        name for name in names
        if name == "research/__init__.py"
        or (name.startswith(PREFIXES) and name.endswith(".py"))
    ]
    rows = []
    files = {}
    for name in selected:
        data = subprocess.check_output(["git", "show", f"HEAD:{name}"], cwd=ROOT)
        files[name] = data
        rows.append({"path": name, "bytes": len(data),
                     "sha256": hashlib.sha256(data).hexdigest(),
                     "git_blob": subprocess.check_output(
                         ["git", "rev-parse", f"HEAD:{name}"], cwd=ROOT,
                         text=True).strip()})
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, data in sorted(files.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(data), 0o644, 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb", filename="", mtime=0,
                       compresslevel=9) as stream:
        stream.write(raw.getvalue())
    archive_bytes = compressed.getvalue()
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    args.archive.write_bytes(archive_bytes)
    manifest = {
        "schema": "v39-telemetry-python-support-v1",
        "git_commit": commit,
        "files": rows,
        "archive_bytes": len(archive_bytes),
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
    }
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
    print(json.dumps({"files": len(rows), "archive_bytes": len(archive_bytes),
                      "archive_sha256": manifest["archive_sha256"]}))


if __name__ == "__main__":
    main()
