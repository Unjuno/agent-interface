"""Restore retained evidence bytes only; never execute archived code."""
from __future__ import annotations
import hashlib, io, json, sys, zipfile
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def safe_name(name: str) -> bool:
    if not isinstance(name, str) or not name or "\\" in name:
        return False
    p = PurePosixPath(name)
    return (not p.is_absolute() and ".." not in p.parts
            and "." not in p.parts and str(p) == name)

def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: restore_evidence.py DEST")
    dst = Path(sys.argv[1])
    if dst.exists() or dst.is_symlink():
        raise SystemExit("destination exists")
    meta = json.loads((HERE / "ARCHIVE.json").read_text(encoding="utf-8"))
    raw = (HERE / meta["path"]).read_bytes()
    if len(raw) != meta["zip_bytes"] or sha(raw) != meta["zip_sha256"]:
        raise SystemExit("zip identity mismatch")

    with zipfile.ZipFile(io.BytesIO(raw), "r") as zf:
        infos = zf.infolist()
        if len(infos) != meta["members"]:
            raise SystemExit("member count mismatch")
        total = 0
        names = set()
        for info in infos:
            name = info.filename
            if (not safe_name(name) or info.is_dir() or name in names
                    or info.file_size < 0):
                raise SystemExit("unsafe/duplicate member")
            names.add(name)
            total += info.file_size
        if total != meta["expanded_bytes"]:
            raise SystemExit("expanded byte mismatch")

        # All metadata are checked before any output is created.
        dst.mkdir(parents=True, exist_ok=False)
        for info in infos:
            out = dst / info.filename
            out.parent.mkdir(parents=True, exist_ok=True)
            data = zf.read(info)
            if len(data) != info.file_size:
                raise SystemExit("member read mismatch")
            with out.open("xb") as f:
                f.write(data)

    print(json.dumps({
        "restored_files": len(infos),
        "restored_bytes": total,
        "zip_sha256": meta["zip_sha256"],
        "scientific_runs": 0
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
