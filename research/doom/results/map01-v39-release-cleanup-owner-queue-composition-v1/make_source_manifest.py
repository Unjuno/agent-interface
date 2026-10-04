import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = [
    ("research/doom/doom_typed_release_backend_v3.py", "23c228146a34ccaa71dafce153532703f04e4d23", "research/doom/doom_typed_release_backend_v3.py"),
    ("research/doom/doom_typed_release_backend_v3_parent.py", "fbed929f629dabaa9ae752019d0ee7151d4d2298", "research/doom/doom_typed_release_backend_v3.py"),
    ("research/live_control/input_transition_owner_v3.py", "fbed929f629dabaa9ae752019d0ee7151d4d2298", "research/live_control/input_transition_owner_v3.py"),
    ("research/live_control/input_owner_v10.py", "13bab54ea6d91978247ecc1b70e5060db752367a", "research/live_control/input_owner_v10.py"),
]
rows = []
for rel, ref, upstream_path in SOURCES:
    local_path = ROOT / rel
    data = local_path.read_bytes()
    # Git's blob ID is SHA-1 over the canonical object header and raw bytes.
    local_git_blob = hashlib.sha1(
        f"blob {len(data)}\0".encode("ascii") + data).hexdigest()
    upstream_blob = {
        "research/doom/doom_typed_release_backend_v3.py": "98e69b734f85f13b956fbeb6922812f2959ee63d",
        "research/doom/doom_typed_release_backend_v3_parent.py": "1515341081f3bbee2ca9587d1c937d398719f05b",
        "research/live_control/input_transition_owner_v3.py": "0ea631abcf6272f0538a9ef9198ad8069b47b464",
        "research/live_control/input_owner_v10.py": "341b3c01649943ddaad5f28431a792c4889cc36e",
    }[rel]
    rows.append({
        "path": rel.replace("\\", "/"),
        "upstream_path": upstream_path,
        "upstream_commit": ref,
        "upstream_git_blob_sha": upstream_blob,
        "local_git_blob_sha": local_git_blob,
        "exact_git_blob_match": local_git_blob == upstream_blob,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })
manifest = {"schema": "map01-v39-release-cleanup-composition-sources-v1",
            "files": rows}
(ROOT / "SOURCE_MANIFEST.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2, sort_keys=True))
if not all(row["exact_git_blob_match"] for row in rows):
    raise SystemExit("one or more copied source files are not byte-identical to Git")
