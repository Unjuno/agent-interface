"""Read-only Git-tree audit of the retained r87-c11 file manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
BASE = "research/integration/issue57_calc_sameframe_live_20261103_r87/r87-c11/"
MANIFEST = BASE + "SHA256SUMS.json"
REVISION = sys.argv[1] if len(sys.argv) > 1 else "HEAD"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO)


def main() -> int:
    try:
        manifest = json.loads(git("show", f"{REVISION}:{MANIFEST}"))
    except subprocess.CalledProcessError:
        print(json.dumps({"revision": REVISION, "status": "packet_absent"}, indent=2))
        return 2

    listing = git("ls-tree", "-r", "-z", REVISION, "--", BASE)
    blobs: dict[str, str] = {}
    for record in listing.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        oid = metadata.decode("ascii").split()[2]
        path = raw_path.decode("utf-8")
        blobs[path[len(BASE):]] = oid

    verified: list[str] = []
    missing: list[str] = []
    mismatched: list[dict[str, object]] = []
    for row in manifest["files"]:
        path = row["path"]
        oid = blobs.get(path)
        if oid is None:
            missing.append(path)
            continue
        data = git("cat-file", "blob", oid)
        digest = hashlib.sha256(data).hexdigest()
        if len(data) == row["bytes"] and digest == row["sha256"]:
            verified.append(path)
        else:
            mismatched.append({
                "path": path,
                "tree_bytes": len(data),
                "manifest_bytes": row["bytes"],
                "tree_sha256": digest,
                "manifest_sha256": row["sha256"],
            })

    result = {
        "revision": REVISION,
        "status": "custody_mismatch" if missing or mismatched else "verified",
        "manifest_entries": len(manifest["files"]),
        "tracked_packet_files": len(blobs),
        "verified": len(verified),
        "missing": missing,
        "mismatched": mismatched,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if missing or mismatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
