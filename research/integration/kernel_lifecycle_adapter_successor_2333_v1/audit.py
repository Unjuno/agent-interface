import json
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

def blob(path):
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=REPO, text=True).strip()

def main():
    manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert len(manifest["sources"]) == 4
    for source in manifest["sources"]:
        path = REPO / source["path"]
        assert path.is_file(), source["path"]
        assert blob(path) == source["blob_sha"], source["path"]
    output = subprocess.check_output([sys.executable, str(ROOT / "run.py")], cwd=REPO, text=True)
    payload = json.loads(output)
    assert payload["schema"] == "agent-interface/kernel-lifecycle-adapter-v1"
    positive = payload["positive"]
    assert positive == {
        "path": "positive", "stage": "verified",
        "effect_verified": True, "release_verified": True,
        "command_id": "command-1",
    }
    negative = payload["negative"]
    assert negative["stale_binding"]["rejected"]
    assert negative["expired_lease"]["rejected"]
    assert negative["nonempty_release"]["rejected"]
    assert negative["verified_stop"] == {"stage": "stopped", "release_verified": True}
    assert negative["unknown_boundary"]["rejected"]
    print("KERNEL_LIFECYCLE_AUDIT_PASS positive=verified negative_rejections=4 source_blobs=4")
    return payload

if __name__ == "__main__":
    main()
